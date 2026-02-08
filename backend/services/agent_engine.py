"""
精進旅程 Agent 引擎
負責：
1. 組裝對話上下文（system prompt + 歷史消息 + 學生檔案）
2. 調用 AI 獲取流式回覆
3. 解析回覆中的 ACTION / PHASE_COMPLETE 標記
4. 執行副作用（保存數據到對應模組表）
5. 管理階段流轉
"""
import json
import re
import logging
from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm.attributes import flag_modified

from database.models import (
    Conversation, ChatMessage, TimeEntry, Goal, ActionPlan, LearningRecord,
)
from services.ai_service import chat_completion_stream
from services.learning_engine import get_student_full, student_to_context
from prompts.agent_prompts import (
    build_agent_system_prompt, get_phase_opening,
    PHASES, PHASE_ORDER,
)
from prompts.templates import build_student_context

logger = logging.getLogger("jingjin.agent")

# ===================== 標記解析 =====================

ACTION_PATTERN = re.compile(r"<!--ACTION:(.*?)-->", re.DOTALL)
PHASE_COMPLETE_PATTERN = re.compile(r"<!--PHASE_COMPLETE:(.*?)-->", re.DOTALL)


def parse_markers(text: str) -> tuple[str, Optional[dict], Optional[dict]]:
    """
    從 AI 回覆中提取 ACTION 和 PHASE_COMPLETE 標記。
    返回 (clean_text, action_data, phase_complete_data)
    """
    action_data = None
    phase_data = None

    # 提取 ACTION
    action_match = ACTION_PATTERN.search(text)
    if action_match:
        try:
            action_data = json.loads(action_match.group(1))
        except json.JSONDecodeError:
            logger.warning(f"無法解析 ACTION 標記: {action_match.group(1)}")

    # 提取 PHASE_COMPLETE
    phase_match = PHASE_COMPLETE_PATTERN.search(text)
    if phase_match:
        try:
            phase_data = json.loads(phase_match.group(1))
        except json.JSONDecodeError:
            logger.warning(f"無法解析 PHASE_COMPLETE 標記: {phase_match.group(1)}")

    # 清理文本（移除標記）
    clean = ACTION_PATTERN.sub("", text)
    clean = PHASE_COMPLETE_PATTERN.sub("", clean).strip()

    return clean, action_data, phase_data


# ===================== 副作用執行 =====================

async def execute_action(
    db: AsyncSession,
    student_id: int,
    conversation: Conversation,
    action: dict,
) -> Optional[dict]:
    """根據 ACTION 標記執行數據保存"""
    action_type = action.get("type", "")
    data = action.get("data", {})
    result = {"type": action_type, "success": False}

    try:
        if action_type == "save_time_entry":
            entry = TimeEntry(
                student_id=student_id,
                activity=data.get("activity", "未命名活動"),
                duration_minutes=data.get("duration_minutes", 30),
                half_life=data.get("half_life", "long"),
                benefit_value=data.get("benefit_value", 3),
            )
            db.add(entry)
            await db.flush()
            result["success"] = True
            result["entry_id"] = entry.id
            logger.info(f"Agent 保存時間記錄: {entry.activity}")

        elif action_type == "save_goal":
            goal = Goal(
                student_id=student_id,
                scenario=conversation.scenario,
                title=data.get("title", "未命名目標"),
                description=data.get("description"),
                five_year_vision=data.get("five_year_vision"),
            )
            db.add(goal)
            await db.flush()
            result["success"] = True
            result["goal_id"] = goal.id
            logger.info(f"Agent 保存目標: {goal.title}")

        elif action_type == "save_action_plan":
            plan = ActionPlan(
                student_id=student_id,
                title=data.get("title", "未命名計劃"),
                core_tasks=data.get("core_tasks", []),
                support_tasks=data.get("support_tasks", []),
            )
            db.add(plan)
            await db.flush()
            result["success"] = True
            result["plan_id"] = plan.id
            logger.info(f"Agent 保存行動計劃: {plan.title}")

        elif action_type == "save_learning_record":
            record = LearningRecord(
                student_id=student_id,
                module=data.get("module", "learning_dojo"),
                scenario=conversation.scenario,
                content=data.get("content", ""),
            )
            db.add(record)
            await db.flush()
            result["success"] = True
            result["record_id"] = record.id
            logger.info(f"Agent 保存學習記錄")

        else:
            logger.warning(f"未知 ACTION 類型: {action_type}")

    except Exception as e:
        logger.error(f"執行 ACTION 失敗: {e}")
        result["error"] = str(e)

    return result


async def advance_phase(
    db: AsyncSession,
    conversation: Conversation,
    phase_complete_data: dict,
) -> Optional[str]:
    """推進到下一階段，返回新的階段 key"""
    current = conversation.current_phase
    phase_def = PHASES.get(current)
    if not phase_def:
        return None

    # 保存當前階段小結到 phase_context
    ctx = dict(conversation.phase_context or {})
    ctx[current] = {
        "summary": phase_complete_data.get("summary", "已完成"),
    }
    conversation.phase_context = ctx
    flag_modified(conversation, "phase_context")

    # 推進到下一階段
    next_phase = phase_def.get("next")
    if next_phase:
        conversation.current_phase = next_phase
        logger.info(f"階段流轉: {current} -> {next_phase}")
        return next_phase
    else:
        conversation.status = "completed"
        logger.info("精進旅程已完成！")
        return None


# ===================== 對話上下文組裝 =====================

async def build_messages(
    db: AsyncSession,
    conversation: Conversation,
    user_message: str,
) -> list[dict]:
    """組裝發送給 AI 的完整 messages 列表"""
    student = await get_student_full(db, conversation.student_id)
    student_ctx_str = build_student_context(student_to_context(student)) if student else ""

    # 組裝 system prompt
    system_prompt = build_agent_system_prompt(
        phase_key=conversation.current_phase,
        scenario=conversation.scenario.value if hasattr(conversation.scenario, 'value') else str(conversation.scenario),
        student_context=student_ctx_str,
        phase_context=conversation.phase_context or {},
    )

    messages = [{"role": "system", "content": system_prompt}]

    # 加入歷史消息（最近 30 條，避免 token 過長）
    history = conversation.messages[-30:] if conversation.messages else []
    for msg in history:
        if msg.role in ("user", "assistant"):
            # 對 assistant 消息清理掉標記
            content = msg.content
            if msg.role == "assistant":
                content = ACTION_PATTERN.sub("", content)
                content = PHASE_COMPLETE_PATTERN.sub("", content).strip()
            messages.append({"role": msg.role, "content": content})

    # 加入當前用戶消息
    messages.append({"role": "user", "content": user_message})

    return messages


# ===================== 流式對話主函數 =====================

async def agent_chat_stream(
    db: AsyncSession,
    conversation: Conversation,
    user_message: str,
) -> AsyncGenerator[str, None]:
    """
    Agent 對話主流程（流式）
    1. 保存用戶消息
    2. 組裝上下文
    3. 調用 AI 流式回覆
    4. 收集完整回覆後解析標記
    5. 執行副作用
    6. 保存 AI 回覆
    7. yield 清理後的文本 chunk
    """
    # 1. 保存用戶消息
    user_msg = ChatMessage(
        conversation_id=conversation.id,
        role="user",
        content=user_message,
        phase_at_time=conversation.current_phase,
    )
    db.add(user_msg)
    await db.flush()

    # 2. 組裝上下文
    messages = await build_messages(db, conversation, user_message)

    # 3. 流式調用 AI — 帶末尾緩衝，避免標記閃爍
    #    策略：緩衝最後 N 個字符。如果緩衝區內無標記起始符 "<!--"，
    #    就安全地 flush 給前端；否則繼續緩衝直到流結束再統一處理。
    MARKER_PREFIX = "<!--"
    BUFFER_SIZE = 6  # 緩衝足夠檢測 "<!--" 的字符數

    full_response = ""
    buffer = ""
    try:
        stream = chat_completion_stream(messages)
        async for chunk in stream:
            full_response += chunk
            buffer += chunk

            # 檢查緩衝區是否包含可能的標記起始
            marker_pos = buffer.find(MARKER_PREFIX)
            if marker_pos >= 0:
                # 標記起始之前的內容可以安全輸出
                if marker_pos > 0:
                    yield buffer[:marker_pos]
                # 把標記及之後的內容留在緩衝區
                buffer = buffer[marker_pos:]
            elif len(buffer) > BUFFER_SIZE:
                # 沒有標記跡象，輸出除最後 BUFFER_SIZE 個字符外的內容
                safe = buffer[:-BUFFER_SIZE]
                buffer = buffer[-BUFFER_SIZE:]
                yield safe
    except Exception as e:
        logger.error(f"AI 調用失敗: {e}")
        error_msg = "抱歉，AI 服務暫時不可用，請稍後再試。"
        full_response = error_msg
        buffer = error_msg

    # 流結束：清理緩衝區，移除標記後輸出剩餘文本
    remaining = ACTION_PATTERN.sub("", buffer)
    remaining = PHASE_COMPLETE_PATTERN.sub("", remaining).strip()
    if remaining:
        yield remaining

    # 4. 解析標記
    clean_text, action_data, phase_data = parse_markers(full_response)

    # 5. 構建消息 action_metadata
    msg_metadata = {}

    # 6. 執行 ACTION
    if action_data:
        action_result = await execute_action(
            db, conversation.student_id, conversation, action_data
        )
        msg_metadata["action"] = action_result

    # 7. 執行 PHASE_COMPLETE
    new_phase = None
    if phase_data:
        new_phase = await advance_phase(db, conversation, phase_data)
        msg_metadata["phase_complete"] = {
            "summary": phase_data.get("summary", ""),
            "new_phase": new_phase,
        }

    # 8. 保存 AI 回覆
    ai_msg = ChatMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=full_response,
        phase_at_time=conversation.current_phase,
        action_metadata=msg_metadata if msg_metadata else None,
    )
    db.add(ai_msg)

    # 更新 conversation 時間
    from datetime import datetime
    conversation.updated_at = datetime.utcnow()

    await db.flush()


async def start_conversation_stream(
    db: AsyncSession,
    conversation: Conversation,
) -> AsyncGenerator[str, None]:
    """
    啟動新對話 — 讓 AI 發出第一條引導消息
    """
    opening_hint = get_phase_opening(
        conversation.current_phase,
        conversation.phase_context or {},
    )

    # 用 system hint 作為用戶消息來觸發 AI 的開場白
    messages = await build_messages(db, conversation, opening_hint)

    full_response = ""
    buffer = ""
    MARKER_PREFIX = "<!--"
    BUFFER_SIZE = 6

    try:
        stream = chat_completion_stream(messages)
        async for chunk in stream:
            full_response += chunk
            buffer += chunk

            marker_pos = buffer.find(MARKER_PREFIX)
            if marker_pos >= 0:
                if marker_pos > 0:
                    yield buffer[:marker_pos]
                buffer = buffer[marker_pos:]
            elif len(buffer) > BUFFER_SIZE:
                safe = buffer[:-BUFFER_SIZE]
                buffer = buffer[-BUFFER_SIZE:]
                yield safe
    except Exception as e:
        logger.error(f"AI 開場調用失敗: {e}")
        error_msg = "抱歉，AI 服務暫時不可用，請稍後再試。"
        full_response = error_msg
        buffer = error_msg

    remaining = ACTION_PATTERN.sub("", buffer)
    remaining = PHASE_COMPLETE_PATTERN.sub("", remaining).strip()
    if remaining:
        yield remaining

    # 解析並保存
    clean_text, action_data, phase_data = parse_markers(full_response)

    ai_msg = ChatMessage(
        conversation_id=conversation.id,
        role="assistant",
        content=full_response,
        phase_at_time=conversation.current_phase,
    )
    db.add(ai_msg)
    await db.flush()
