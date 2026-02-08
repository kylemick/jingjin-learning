"""
本地語音轉文字服務 — 基於 faster-whisper (離線，無需外網)
首次使用會自動下載 Whisper base 模型 (~150MB)
"""
import os
import tempfile
import logging
import asyncio

logger = logging.getLogger("jingjin.stt")

# 設置 HuggingFace 鏡像（中國大陸加速下載模型）
os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")

_model = None
_model_loading = False


def _get_model():
    """懶加載 Whisper 模型（僅在首次調用時加載）"""
    global _model, _model_loading

    if _model is not None:
        return _model

    if _model_loading:
        raise RuntimeError("模型正在加載中，請稍候再試")

    _model_loading = True
    try:
        from faster_whisper import WhisperModel

        model_size = os.environ.get("WHISPER_MODEL", "base")
        logger.info(f"正在加載 Whisper 語音識別模型 ({model_size})...")
        logger.info("  首次加載需下載模型文件，請耐心等待...")

        _model = WhisperModel(
            model_size,
            device="cpu",
            compute_type="int8",
        )
        logger.info(f"✓ Whisper {model_size} 模型加載完成")
        return _model
    except ImportError:
        _model_loading = False
        raise RuntimeError(
            "faster-whisper 未安裝。請執行: pip install faster-whisper"
        )
    except Exception as e:
        _model_loading = False
        raise RuntimeError(f"Whisper 模型加載失敗: {e}")


def _transcribe_sync(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """同步轉寫音頻"""
    model = _get_model()

    # 根據檔名推斷後綴
    suffix = ".webm"
    if filename:
        ext = os.path.splitext(filename)[1]
        if ext:
            suffix = ext

    # 寫入臨時文件
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as f:
        f.write(audio_bytes)
        tmp_path = f.name

    try:
        segments, info = model.transcribe(
            tmp_path,
            language="zh",
            vad_filter=True,  # 過濾靜音段，提升速度
            vad_parameters=dict(min_silence_duration_ms=500),
        )
        text = "".join(segment.text for segment in segments)
        duration = round(info.duration, 1)
        logger.info(f"  轉寫完成: {duration}s 音頻 → {len(text)} 字")
        return text.strip()
    finally:
        os.unlink(tmp_path)


async def transcribe_audio(audio_bytes: bytes, filename: str = "audio.webm") -> str:
    """異步轉寫音頻（在線程池中執行，不阻塞事件循環）"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _transcribe_sync, audio_bytes, filename)


def is_whisper_available() -> bool:
    """檢查 faster-whisper 是否可用"""
    try:
        import faster_whisper  # noqa: F401
        return True
    except ImportError:
        return False
