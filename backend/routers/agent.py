"""精進旅程 Agent 路由 — 引導式對話"""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.connection import get_db, async_session
from database.models import Conversation, ChatMessage
from schemas import (
    ConversationCreate, ConversationOut, ConversationDetailOut,
    ChatMessageOut, AgentChatRequest,
)
from services.agent_engine import agent_chat_stream, start_conversation_stream
from prompts.agent_prompts import PHASES, PHASE_ORDER

router = APIRouter()
logger = logging.getLogger("jingjin.agent")


@router.post("/{student_id}/conversations", response_model=ConversationOut)
async def create_conversation(
    student_id: int,
    data: ConversationCreate,
    db: AsyncSession = Depends(get_db),
):
    """創建新的精進旅程對話"""
    conv = Conversation(
        student_id=student_id,
        title=data.title or "新的精進旅程",
        scenario=data.scenario,
        current_phase="time_compass",
        phase_context={},
    )
    db.add(conv)
    await db.flush()
    await db.refresh(conv)
    logger.info(f"創建旅程對話: student={student_id}, conv={conv.id}")
    return conv


@router.get("/{student_id}/conversations", response_model=list[ConversationOut])
async def list_conversations(
    student_id: int,
    db: AsyncSession = Depends(get_db),
):
    """列出學生的所有對話"""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.student_id == student_id)
        .order_by(Conversation.updated_at.desc())
    )
    return result.scalars().all()


@router.get("/{student_id}/conversations/{conv_id}", response_model=ConversationDetailOut)
async def get_conversation(
    student_id: int,
    conv_id: int,
    db: AsyncSession = Depends(get_db),
):
    """獲取對話詳情（含歷史消息）"""
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conv_id, Conversation.student_id == student_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="對話不存在")
    return conv


@router.post("/{student_id}/conversations/{conv_id}/start")
async def start_conversation(student_id: int, conv_id: int):
    """啟動對話 — AI 發出第一條引導消息（SSE 流式）
    使用自管理的 DB session 確保 StreamingResponse 期間 session 有效。
    """

    async def event_generator():
        async with async_session() as db:
            try:
                result = await db.execute(
                    select(Conversation)
                    .options(selectinload(Conversation.messages))
                    .where(Conversation.id == conv_id, Conversation.student_id == student_id)
                )
                conv = result.scalar_one_or_none()
                if not conv:
                    yield f"data: {json.dumps({'error': '對話不存在'}, ensure_ascii=False)}\n\n"
                    yield "data: [DONE]\n\n"
                    return

                if conv.messages:
                    yield f"data: {json.dumps({'error': '對話已啟動'}, ensure_ascii=False)}\n\n"
                    yield "data: [DONE]\n\n"
                    return

                stream = start_conversation_stream(db, conv)
                async for chunk in stream:
                    yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"

                await db.commit()
                yield "data: [DONE]\n\n"
            except Exception as e:
                await db.rollback()
                logger.error(f"Start conversation error: {e}")
                yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/{student_id}/conversations/{conv_id}/chat")
async def chat(student_id: int, conv_id: int, data: AgentChatRequest):
    """發送消息並獲取 AI 回覆（SSE 流式）
    使用自管理的 DB session 確保 StreamingResponse 期間 session 有效。
    """
    message = data.message

    async def event_generator():
        async with async_session() as db:
            try:
                result = await db.execute(
                    select(Conversation)
                    .options(selectinload(Conversation.messages))
                    .where(Conversation.id == conv_id, Conversation.student_id == student_id)
                )
                conv = result.scalar_one_or_none()
                if not conv:
                    yield f"data: {json.dumps({'error': '對話不存在'}, ensure_ascii=False)}\n\n"
                    yield "data: [DONE]\n\n"
                    return

                stream = agent_chat_stream(db, conv, message)
                async for chunk in stream:
                    yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"

                await db.commit()

                # 發送最終的對話狀態更新
                await db.refresh(conv)
                state = {
                    "type": "state_update",
                    "current_phase": conv.current_phase,
                    "phase_context": conv.phase_context,
                    "status": conv.status.value if hasattr(conv.status, 'value') else str(conv.status),
                }
                yield f"data: {json.dumps(state, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"
            except Exception as e:
                await db.rollback()
                logger.error(f"Chat error: {e}")
                yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"
                yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/{student_id}/conversations/{conv_id}/skip-phase")
async def skip_phase(
    student_id: int,
    conv_id: int,
    db: AsyncSession = Depends(get_db),
):
    """跳過當前階段，進入下一階段"""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conv_id, Conversation.student_id == student_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="對話不存在")

    current = conv.current_phase
    phase_def = PHASES.get(current)
    if not phase_def or not phase_def.get("next"):
        return {"ok": False, "message": "已是最後階段"}

    next_phase = phase_def["next"]

    # 更新 phase_context (dict copy + flag_modified 確保 JSON 欄位更新被追蹤)
    from sqlalchemy.orm.attributes import flag_modified
    ctx = dict(conv.phase_context or {})
    ctx[current] = {"summary": "（已跳過）"}
    conv.phase_context = ctx
    flag_modified(conv, "phase_context")
    conv.current_phase = next_phase
    await db.flush()

    phase_info = PHASES.get(next_phase, {})
    return {
        "ok": True,
        "new_phase": next_phase,
        "phase_name": phase_info.get("name", next_phase),
    }


@router.get("/phases")
async def get_phases():
    """獲取所有階段定義（前端渲染進度條用）"""
    return {
        "phases": [
            {
                "key": key,
                "order": PHASES[key]["order"],
                "name": PHASES[key]["name"],
                "book_chapter": PHASES[key]["book_chapter"],
                "goal": PHASES[key]["goal"],
            }
            for key in PHASE_ORDER
        ]
    }
