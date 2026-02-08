"""
DeepSeek AI 服務封裝
支持流式 (SSE) 和非流式調用
"""
import json
from typing import AsyncGenerator, Optional
import httpx
from config import get_settings
from prompts.templates import build_full_prompt

settings = get_settings()

DEEPSEEK_CHAT_URL = f"{settings.DEEPSEEK_BASE_URL}/v1/chat/completions"


async def chat_completion(
    messages: list[dict],
    model: str = "deepseek-chat",
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> str:
    """非流式調用 DeepSeek API"""
    headers = {
        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(DEEPSEEK_CHAT_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def chat_completion_stream(
    messages: list[dict],
    model: str = "deepseek-chat",
    temperature: float = 0.7,
    max_tokens: int = 2000,
) -> AsyncGenerator[str, None]:
    """流式調用 DeepSeek API，逐 token 返回"""
    headers = {
        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream("POST", DEEPSEEK_CHAT_URL, headers=headers, json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data_str = line[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        data = json.loads(data_str)
                        delta = data["choices"][0].get("delta", {})
                        content = delta.get("content", "")
                        if content:
                            yield content
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue


async def get_ai_response(
    module: str,
    scenario: Optional[str],
    student_info: Optional[dict],
    user_message: str,
    stream: bool = True,
) -> AsyncGenerator[str, None] | str:
    """
    精進學習系統的統一 AI 調用接口

    自動組裝 system prompt（模組 + 場景 + 個人檔案）
    """
    system_prompt = build_full_prompt(module, scenario, student_info)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    if stream:
        return chat_completion_stream(messages)
    else:
        return await chat_completion(messages)


async def get_ai_response_full(
    module: str,
    scenario: Optional[str],
    student_info: Optional[dict],
    user_message: str,
) -> str:
    """非流式版本，返回完整回覆"""
    system_prompt = build_full_prompt(module, scenario, student_info)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    return await chat_completion(messages)
