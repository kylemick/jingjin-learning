import logging
import sys
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from database.connection import init_db

# ===================== 統一日誌配置 =====================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
# 降低第三方庫日誌級別
logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger("jingjin")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 50)
    logger.info("精進學習系統 - 啟動中")
    logger.info("=" * 50)
    try:
        await init_db()
        logger.info("✓ 數據庫初始化完成")
    except Exception as e:
        logger.error(f"✗ 數據庫初始化失敗: {e}")
        raise
    logger.info("✓ 後端服務就緒 (http://localhost:8000)")
    logger.info("  API 文檔: http://localhost:8000/docs")
    logger.info("=" * 50)
    yield
    logger.info("精進學習系統 - 已停止")


app = FastAPI(
    title="精進學習系統",
    description="基於《精進：如何成為一個很厲害的人》的中學生學習提升平台",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 延遲導入路由，避免循環引用
from routers import (
    profile,
    question_bank,
    time_compass,
    choice_navigator,
    action_workshop,
    learning_dojo,
    thinking_forge,
    talent_growth,
    review_hub,
    voice,
)

app.include_router(profile.router, prefix="/api/profile", tags=["個人檔案"])
app.include_router(question_bank.router, prefix="/api/questions", tags=["題庫"])
app.include_router(time_compass.router, prefix="/api/time-compass", tags=["時間羅盤"])
app.include_router(choice_navigator.router, prefix="/api/choice-navigator", tags=["選擇導航"])
app.include_router(action_workshop.router, prefix="/api/action-workshop", tags=["行動工坊"])
app.include_router(learning_dojo.router, prefix="/api/learning-dojo", tags=["學習道場"])
app.include_router(thinking_forge.router, prefix="/api/thinking-forge", tags=["思維鍛造"])
app.include_router(talent_growth.router, prefix="/api/talent-growth", tags=["才能精進"])
app.include_router(review_hub.router, prefix="/api/review-hub", tags=["成長復盤"])
app.include_router(voice.router, prefix="/api/voice", tags=["語音交互"])


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "精進學習系統運行中"}
