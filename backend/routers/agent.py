"""精進旅程 Agent 路由 — 引導式對話"""
import json
import re
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.connection import get_db, async_session
from database.models import (
    Conversation, ChatMessage, TimeEntry, Goal, ActionPlan, LearningRecord,
)
from schemas import (
    ConversationCreate, ConversationUpdate, ConversationOut,
    ConversationDetailOut, ChatMessageOut, AgentChatRequest,
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


@router.patch("/{student_id}/conversations/{conv_id}", response_model=ConversationOut)
async def update_conversation(
    student_id: int,
    conv_id: int,
    data: ConversationUpdate,
    db: AsyncSession = Depends(get_db),
):
    """更新對話（重命名等）"""
    result = await db.execute(
        select(Conversation)
        .where(Conversation.id == conv_id, Conversation.student_id == student_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="對話不存在")
    conv.title = data.title
    await db.flush()
    await db.refresh(conv)
    return conv


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


@router.get("/{student_id}/conversations/{conv_id}/export")
async def export_conversation(
    student_id: int,
    conv_id: int,
    db: AsyncSession = Depends(get_db),
):
    """導出旅程為 Markdown 文件"""
    ACTION_RE = re.compile(r"<!--ACTION:.*?-->", re.DOTALL)
    PHASE_RE = re.compile(r"<!--PHASE_COMPLETE:.*?-->", re.DOTALL)

    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(Conversation.id == conv_id, Conversation.student_id == student_id)
    )
    conv = result.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="對話不存在")

    scenario_label = {"academic": "學科提升", "expression": "表達提升", "interview": "面試提升"}
    status_label = {"active": "進行中", "completed": "已完成", "archived": "已歸檔"}
    phase_names = {p: PHASES[p]["name"] for p in PHASE_ORDER}

    lines: list[str] = []

    # --- Header ---
    lines.append(f"# 精進旅程：{conv.title}")
    lines.append("")
    scn = conv.scenario.value if hasattr(conv.scenario, "value") else str(conv.scenario)
    sts = conv.status.value if hasattr(conv.status, "value") else str(conv.status)
    lines.append(f"- **場景**：{scenario_label.get(scn, scn)}")
    lines.append(f"- **狀態**：{status_label.get(sts, sts)}")
    created = conv.created_at.strftime("%Y-%m-%d %H:%M") if conv.created_at else "—"
    updated = conv.updated_at.strftime("%Y-%m-%d %H:%M") if conv.updated_at else "—"
    lines.append(f"- **時間**：{created} ~ {updated}")
    lines.append("")

    # --- Phase overview ---
    lines.append("## 旅程總覽")
    lines.append("")
    ctx = conv.phase_context or {}
    current_idx = PHASE_ORDER.index(conv.current_phase) if conv.current_phase in PHASE_ORDER else 0
    for i, key in enumerate(PHASE_ORDER):
        name = phase_names[key]
        if key in ctx:
            mark = "[x]"
        elif i == current_idx and sts != "completed":
            mark = "[-]"  # current
        else:
            mark = "[ ]"
        lines.append(f"- {mark} **{i+1}. {name}** — {PHASES[key]['book_chapter']}")
    lines.append("")

    # --- Phase summaries ---
    if ctx:
        lines.append("## 各階段成果")
        lines.append("")
        for key in PHASE_ORDER:
            if key not in ctx:
                continue
            phase_data = ctx[key]
            name = phase_names[key]
            summary = phase_data.get("summary", "") if isinstance(phase_data, dict) else str(phase_data)
            lines.append(f"### {PHASES[key]['order']}. {name}")
            lines.append("")
            lines.append(f"**小結**：{summary}")
            lines.append("")

    # --- Chat transcript ---
    lines.append("## 完整對話記錄")
    lines.append("")
    for msg in conv.messages:
        if msg.role == "system":
            continue
        role_label = "學生" if msg.role == "user" else "教練"
        phase_label = phase_names.get(msg.phase_at_time, msg.phase_at_time or "")
        # Clean markers
        content = ACTION_RE.sub("", msg.content)
        content = PHASE_RE.sub("", content).strip()
        ts = msg.created_at.strftime("%H:%M") if msg.created_at else ""
        lines.append(f"**{role_label}**（{phase_label} {ts}）：")
        lines.append("")
        lines.append(content)
        lines.append("")
        lines.append("---")
        lines.append("")

    # --- Action data ---
    # Query related data created during this conversation's timeframe
    if conv.created_at:
        time_result = await db.execute(
            select(TimeEntry)
            .where(TimeEntry.student_id == student_id, TimeEntry.date >= conv.created_at)
            .order_by(TimeEntry.date)
        )
        entries = time_result.scalars().all()

        goal_result = await db.execute(
            select(Goal)
            .where(Goal.student_id == student_id, Goal.created_at >= conv.created_at)
            .order_by(Goal.created_at)
        )
        goals = goal_result.scalars().all()

        plan_result = await db.execute(
            select(ActionPlan)
            .where(ActionPlan.student_id == student_id, ActionPlan.created_at >= conv.created_at)
            .order_by(ActionPlan.created_at)
        )
        plans = plan_result.scalars().all()

        has_data = entries or goals or plans
        if has_data:
            lines.append("## 行動數據")
            lines.append("")

            if entries:
                lines.append("### 時間記錄")
                lines.append("")
                half_labels = {"long": "長半衰期", "short": "短半衰期"}
                for e in entries:
                    hl = half_labels.get(e.half_life, e.half_life or "")
                    lines.append(f"- {e.activity}（{e.duration_minutes} 分鐘，{hl}，收益值 {e.benefit_value}/5）")
                lines.append("")

            if goals:
                lines.append("### 目標")
                lines.append("")
                for g in goals:
                    lines.append(f"- **{g.title}**")
                    if g.description:
                        lines.append(f"  - 描述：{g.description}")
                    if g.five_year_vision:
                        lines.append(f"  - 五年願景：{g.five_year_vision}")
                lines.append("")

            if plans:
                lines.append("### 行動計劃")
                lines.append("")
                for p in plans:
                    lines.append(f"- **{p.title}**")
                    if p.core_tasks:
                        lines.append(f"  - 核心任務：{', '.join(p.core_tasks)}")
                    if p.support_tasks:
                        lines.append(f"  - 支撐任務：{', '.join(p.support_tasks)}")
                lines.append("")

    # --- Footer ---
    lines.append("---")
    lines.append("")
    lines.append(f"*由精進學習系統導出 · {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC*")

    md_content = "\n".join(lines)

    # Safe filename — URL-encode for non-ASCII chars (RFC 5987)
    from urllib.parse import quote
    safe_title = conv.title.replace("/", "_")[:30]
    ascii_name = f"jingjin_{conv.id}.md"
    utf8_name = f"jingjin_{conv.id}_{safe_title}.md"

    return Response(
        content=md_content.encode("utf-8"),
        media_type="text/markdown; charset=utf-8",
        headers={
            "Content-Disposition": f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{quote(utf8_name)}"
        },
    )


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
