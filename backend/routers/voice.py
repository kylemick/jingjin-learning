"""語音交互路由"""
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.responses import JSONResponse
from config import get_settings
from services.stt_service import transcribe_audio, is_whisper_available

router = APIRouter()
settings = get_settings()
logger = logging.getLogger("jingjin.voice")


def is_xunfei_configured() -> bool:
    """檢查訊飛 API 是否已配置"""
    return bool(
        settings.XUNFEI_APP_ID
        and settings.XUNFEI_API_KEY
        and settings.XUNFEI_API_SECRET
    )


@router.get("/status")
async def voice_status():
    """語音模組狀態"""
    whisper_ok = is_whisper_available()
    return {
        "stt_engine": "local_whisper" if whisper_ok else "unavailable",
        "tts_engine": "browser_speech_synthesis",
        "whisper_available": whisper_ok,
        "xunfei_configured": is_xunfei_configured(),
        "lang": "zh-TW",
        "message": (
            "本地 Whisper 語音識別已就緒（離線可用）" if whisper_ok
            else "語音識別不可用，請安裝 faster-whisper"
        ),
    }


@router.post("/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    """
    音頻轉文字端點
    前端錄音後上傳音頻文件，後端使用本地 Whisper 模型轉寫
    支持 webm、wav、mp3、m4a 等常見格式
    """
    if not is_whisper_available():
        return JSONResponse(
            status_code=503,
            content={
                "error": "faster-whisper 未安裝",
                "message": "請執行: pip install faster-whisper",
            },
        )

    try:
        audio_bytes = await audio.read()
        if len(audio_bytes) < 100:
            return {"text": "", "message": "音頻太短，未能識別"}

        logger.info(f"收到音頻: {audio.filename}, 大小: {len(audio_bytes)} bytes")
        text = await transcribe_audio(audio_bytes, audio.filename or "audio.webm")

        return {"text": text, "success": True}

    except RuntimeError as e:
        logger.error(f"轉寫失敗: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "text": ""},
        )
    except Exception as e:
        logger.error(f"轉寫異常: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": f"語音識別失敗: {str(e)}", "text": ""},
        )


@router.websocket("/stt")
async def websocket_stt(ws: WebSocket):
    """
    語音聽寫 WebSocket 端點（訊飛代理模式）
    僅在訊飛 API 配置完成後可用
    """
    await ws.accept()

    if not is_xunfei_configured():
        await ws.send_json({
            "type": "error",
            "message": "訊飛 API 未配置，請使用本地 Whisper 語音識別",
        })
        await ws.close()
        return

    try:
        import websockets
        import json
        import asyncio
        from services.voice_service import (
            create_xunfei_auth_url,
            build_stt_first_frame,
            build_stt_continue_frame,
            build_stt_last_frame,
            parse_stt_response,
        )

        xunfei_url = create_xunfei_auth_url()
        logger.info("正在連接訊飛 STT...")

        async with websockets.connect(xunfei_url) as xunfei_ws:
            frame_count = 0

            async def receive_from_xunfei():
                try:
                    async for message in xunfei_ws:
                        text = parse_stt_response(message)
                        if text:
                            await ws.send_json({"type": "result", "text": text})
                        data = json.loads(message)
                        code = data.get("code", 0)
                        if code != 0:
                            logger.error(f"訊飛錯誤: code={code}")
                            await ws.send_json({
                                "type": "error",
                                "message": f"訊飛錯誤: {data.get('message', '')}",
                            })
                            break
                        status = data.get("data", {}).get("status", 0)
                        if status == 2:
                            await ws.send_json({"type": "end"})
                            break
                except Exception as e:
                    logger.error(f"接收訊飛數據異常: {e}")

            receive_task = asyncio.create_task(receive_from_xunfei())

            while True:
                try:
                    data = await ws.receive()
                    if data.get("type") == "websocket.disconnect":
                        break
                    if "bytes" in data:
                        audio_bytes = data["bytes"]
                        if frame_count == 0:
                            frame = build_stt_first_frame(audio_bytes)
                        else:
                            frame = build_stt_continue_frame(audio_bytes)
                        await xunfei_ws.send(frame)
                        frame_count += 1
                    elif "text" in data:
                        msg = json.loads(data["text"])
                        if msg.get("type") == "stop":
                            await xunfei_ws.send(build_stt_last_frame())
                            break
                except WebSocketDisconnect:
                    break

            try:
                await asyncio.wait_for(receive_task, timeout=5.0)
            except asyncio.TimeoutError:
                receive_task.cancel()

    except Exception as e:
        logger.error(f"語音 WebSocket 錯誤: {e}")
        try:
            await ws.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass
    finally:
        try:
            await ws.close()
        except Exception:
            pass


@router.get("/tts-config")
async def tts_config():
    """TTS 配置 — 使用瀏覽器 SpeechSynthesis API"""
    return {
        "engine": "browser_speech_synthesis",
        "lang": "zh-TW",
        "rate": 0.9,
        "pitch": 1.0,
        "volume": 1.0,
    }
