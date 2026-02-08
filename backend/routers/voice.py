"""語音交互路由"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from services.voice_service import (
    create_xunfei_auth_url,
    build_stt_first_frame,
    build_stt_continue_frame,
    build_stt_last_frame,
    parse_stt_response,
)
from config import get_settings
import websockets
import json
import asyncio

router = APIRouter()
settings = get_settings()


@router.websocket("/stt")
async def websocket_stt(ws: WebSocket):
    """
    語音聽寫 WebSocket 端點
    前端發送音頻數據，後端轉發到訊飛 API，返回識別結果
    """
    await ws.accept()

    try:
        # 連接到訊飛 WebSocket
        xunfei_url = create_xunfei_auth_url()
        async with websockets.connect(xunfei_url) as xunfei_ws:
            frame_count = 0

            async def receive_from_xunfei():
                """從訊飛接收識別結果並發送給前端"""
                try:
                    async for message in xunfei_ws:
                        text = parse_stt_response(message)
                        if text:
                            await ws.send_json({"type": "result", "text": text})

                        # 檢查是否結束
                        data = json.loads(message)
                        status = data.get("data", {}).get("status", 0)
                        if status == 2:
                            await ws.send_json({"type": "end"})
                            break
                except Exception:
                    pass

            # 啟動接收任務
            receive_task = asyncio.create_task(receive_from_xunfei())

            # 接收前端的音頻數據
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

            # 等待接收完成
            try:
                await asyncio.wait_for(receive_task, timeout=5.0)
            except asyncio.TimeoutError:
                receive_task.cancel()

    except Exception as e:
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
    """
    TTS 配置 - 使用瀏覽器 SpeechSynthesis API
    前端直接使用瀏覽器的語音合成，此端點提供配置信息
    """
    return {
        "engine": "browser_speech_synthesis",
        "lang": "zh-TW",
        "rate": 1.0,
        "pitch": 1.0,
        "volume": 1.0,
    }
