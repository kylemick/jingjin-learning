"""思維鍛造路由 - 修煉思維利器"""
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from database.connection import get_db
from services.ai_service import get_ai_response
from services.learning_engine import get_student_full, student_to_context
import json

router = APIRouter()


@router.post("/{student_id}/socratic-dialogue")
async def socratic_dialogue(
    student_id: int,
    topic: str,
    student_answer: str = "",
    scenario: str = "academic",
    db: AsyncSession = Depends(get_db),
):
    """蘇格拉底式問答 - 層層深入的思維訓練"""
    student = await get_student_full(db, student_id)
    ctx = student_to_context(student) if student else None

    if student_answer:
        message = (
            f"我們在討論的主題是：{topic}\n"
            f"我的回答/想法是：{student_answer}\n\n"
            f"請用蘇格拉底式提問法，針對我的回答進一步追問，幫助我深入思考。"
            f"不要直接給出判斷，而是用問題引導我發現盲點和更深的洞見。"
        )
    else:
        message = (
            f"我想深入思考這個主題：{topic}\n\n"
            f"請用蘇格拉底式提問法開始我們的思維對話。"
            f"從一個基礎但發人深省的問題開始，一步步引導我深入思考。"
        )

    stream = await get_ai_response("thinking_forge", scenario, ctx, message)

    async def event_generator():
        async for chunk in stream:
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/{student_id}/simplify")
async def simplify_thinking(
    student_id: int,
    complex_problem: str,
    db: AsyncSession = Depends(get_db),
):
    """斷捨離簡化練習 - 對複雜問題進行核心提煉"""
    student = await get_student_full(db, student_id)
    ctx = student_to_context(student) if student else None

    message = (
        f"以下是一個複雜的問題/情境：\n{complex_problem}\n\n"
        f"請幫我進行思維「斷捨離」：\n"
        f"1.【捨】哪些是無關緊要的干擾信息？\n"
        f"2.【斷】問題的核心本質是什麼？（用一句話概括）\n"
        f"3.【離】理清思路後，最佳的思考路徑是什麼？\n\n"
        f"引導我一步步簡化，然後用結構化的方式清晰思考。"
    )

    stream = await get_ai_response("thinking_forge", None, ctx, message)

    async def event_generator():
        async for chunk in stream:
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/{student_id}/structured-thinking")
async def structured_thinking(
    student_id: int,
    topic: str,
    thinking_tool: str = "argument",
    db: AsyncSession = Depends(get_db),
):
    """結構化思考模板"""
    student = await get_student_full(db, student_id)
    ctx = student_to_context(student) if student else None

    tool_prompts = {
        "argument": "論點→論據→結論 的三段式結構",
        "matrix": "二維矩陣分析（如優劣勢、重要性-緊迫性）",
        "mindmap": "思維導圖式的發散-收斂思考",
        "timeline": "時間線式的因果鏈分析",
    }

    tool_desc = tool_prompts.get(thinking_tool, tool_prompts["argument"])

    message = (
        f"主題：{topic}\n\n"
        f"請引導我用「{tool_desc}」的方式來組織我的思考。\n"
        f"1. 先幫我理清思考的框架\n"
        f"2. 引導我在每個框架節點填入內容\n"
        f"3. 最後幫我檢查思考的完整性和邏輯性\n\n"
        f"記住：思考可以有自己的形狀，用結構讓思維更清晰。"
    )

    stream = await get_ai_response("thinking_forge", None, ctx, message)

    async def event_generator():
        async for chunk in stream:
            yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
