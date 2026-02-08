"""
訊飛語音服務 - WebSocket 代理
實現語音聽寫 (STT) 功能
"""
import base64
import hashlib
import hmac
import json
import time
from datetime import datetime
from urllib.parse import urlencode, quote
from config import get_settings

settings = get_settings()

XUNFEI_STT_URL = "wss://iat-api.xfyun.cn/v2/iat"


def create_xunfei_auth_url() -> str:
    """生成訊飛 WebSocket 認證 URL"""
    now = datetime.utcnow()
    date = now.strftime("%a, %d %b %Y %H:%M:%S GMT")

    signature_origin = (
        f"host: iat-api.xfyun.cn\n"
        f"date: {date}\n"
        f"GET /v2/iat HTTP/1.1"
    )

    signature_sha = hmac.new(
        settings.XUNFEI_API_SECRET.encode("utf-8"),
        signature_origin.encode("utf-8"),
        digestmod=hashlib.sha256,
    ).digest()

    signature = base64.b64encode(signature_sha).decode("utf-8")

    authorization_origin = (
        f'api_key="{settings.XUNFEI_API_KEY}", '
        f'algorithm="hmac-sha256", '
        f'headers="host date request-line", '
        f'signature="{signature}"'
    )
    authorization = base64.b64encode(authorization_origin.encode("utf-8")).decode("utf-8")

    params = {
        "authorization": authorization,
        "date": date,
        "host": "iat-api.xfyun.cn",
    }

    return f"{XUNFEI_STT_URL}?{urlencode(params)}"


def build_stt_first_frame(audio_data: bytes) -> str:
    """構建語音聽寫的第一幀數據"""
    return json.dumps({
        "common": {"app_id": settings.XUNFEI_APP_ID},
        "business": {
            "language": "zh_cn",
            "domain": "iat",
            "accent": "mandarin",
            "vad_eos": 3000,
            "dwa": "wpgs",
        },
        "data": {
            "status": 0,
            "format": "audio/L16;rate=16000",
            "encoding": "raw",
            "audio": base64.b64encode(audio_data).decode("utf-8"),
        },
    })


def build_stt_continue_frame(audio_data: bytes) -> str:
    """構建語音聽寫的中間幀數據"""
    return json.dumps({
        "data": {
            "status": 1,
            "format": "audio/L16;rate=16000",
            "encoding": "raw",
            "audio": base64.b64encode(audio_data).decode("utf-8"),
        },
    })


def build_stt_last_frame() -> str:
    """構建語音聽寫的最後一幀數據"""
    return json.dumps({
        "data": {
            "status": 2,
            "format": "audio/L16;rate=16000",
            "encoding": "raw",
            "audio": "",
        },
    })


def parse_stt_response(message: str) -> str:
    """解析語音聽寫返回結果"""
    try:
        data = json.loads(message)
        code = data.get("code", -1)
        if code != 0:
            return ""

        result = data.get("data", {}).get("result", {})
        ws_list = result.get("ws", [])
        text = ""
        for ws in ws_list:
            for cw in ws.get("cw", []):
                text += cw.get("w", "")
        return text
    except (json.JSONDecodeError, KeyError):
        return ""
