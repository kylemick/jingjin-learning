# 精進學習系統

> 基於采銅《精進：如何成為一個很厲害的人》核心理念，為中學生打造的 AI 驅動學習提升平台。

盲目的努力，只是一種緩慢的疊加。精準的方法，才能帶來質的飛躍。

## 核心理念 · 七大維度

本系統將《精進》一書的七大維度轉化為可操作的功能模組：

| 模組 | 書中維度 | 核心功能 |
|---|---|---|
| **時間羅盤** | 時間之尺 | 半衰期評估、時間投入記錄、AI 分析時間品質 |
| **選擇導航** | 尋找心中的巴拿馬 | 目標設定、隱含假設識別、第三選擇探索 |
| **行動工坊** | 即刻行動 | 圖層工作法任務分解、MVP 式練習、AI 即時反饋 |
| **學習道場** | 直面現實的學習 | 以問題為中心學習、知識解碼、知識融合 |
| **思維鍛造** | 修煉思維利器 | 蘇格拉底問答、斷捨離簡化、結構化思考 |
| **才能精進** | 優化努力方式 | 長板優勢識別、必要難度挑戰設計、能力畫像 |
| **成長復盤** | 創造獨特成功 | 三行而後思、AI 深度反饋、學習歷程檔案 |

## 三大應用場景

- **學科提升** — 各學科知識學習與練習
- **表達提升** — 邏輯性、語言組織、說服力訓練
- **面試提升** — 模擬面試、回答技巧訓練

## 特色功能

- **個人檔案系統** — 活的數據模型，隨學習過程持續演化，驅動 AI Prompt 動態調整
- **題庫系統** — 支持手動錄入 + AI 動態生成，按難度分級（必要的難度）
- **語音交互** — 語音輸入（訊飛 STT）+ 語音朗讀（瀏覽器 TTS），提升交互體驗
- **AI 流式反饋** — DeepSeek API SSE 流式輸出，即時看到 AI 回覆

## 技術棧

- **前端**: React 18 + TypeScript + Vite + TailwindCSS + Recharts
- **後端**: Python FastAPI + SQLAlchemy (async) + MySQL
- **AI**: DeepSeek API (Chat Completion, SSE)
- **語音**: 訊飛 WebSocket STT + 瀏覽器 SpeechSynthesis TTS

## 快速開始

### 1. 前置條件

- Python 3.11+
- Node.js 18+
- MySQL 8.0+
- DeepSeek API Key

### 2. 配置環境變量

```bash
cp backend/.env.example backend/.env
# 編輯 backend/.env，填入你的 MySQL 密碼和 DeepSeek API Key
```

### 3. 一鍵啟動（推薦）

```bash
./start.sh
```

啟動腳本會自動完成以下操作：
- 檢查 MySQL 連接，自動建立數據庫（如不存在），**不覆蓋已有數據**
- 初始化 Python 虛擬環境和依賴
- 初始化 npm 依賴
- 同時啟動前後端服務，**日誌統一輸出到 console**（帶 `[前端]`/`[後端]` 前綴）
- 按 `Ctrl+C` 可優雅停止所有服務

### 4. 手動啟動（可選）

```bash
# 後端
cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000

# 前端（另開終端）
cd frontend && npm run dev
```

### 5. 訪問系統

打開瀏覽器訪問 `http://localhost:5173`

## 項目結構

```
improve/
├── backend/
│   ├── main.py                  # FastAPI 入口
│   ├── config.py                # 配置管理
│   ├── schemas.py               # Pydantic 數據模型
│   ├── database/
│   │   ├── connection.py        # MySQL 連接
│   │   └── models.py            # ORM 模型
│   ├── services/
│   │   ├── ai_service.py        # DeepSeek API 封裝
│   │   ├── voice_service.py     # 訊飛語音代理
│   │   └── learning_engine.py   # 業務邏輯引擎
│   ├── routers/                 # 各模組 API 路由
│   └── prompts/
│       └── templates.py         # AI Prompt 模板
├── frontend/
│   ├── src/
│   │   ├── components/          # 通用 UI 組件
│   │   ├── pages/               # 頁面組件
│   │   ├── hooks/               # React Hooks
│   │   └── services/            # API 封裝
│   └── ...
└── README.md
```

## API 文檔

啟動後端後，訪問 `http://localhost:8000/docs` 查看 Swagger API 文檔。

## 精進閉環

系統的核心設計是一個持續精進的閉環：

```
個人檔案 → Prompt 動態調整 → 練習/行動 → AI 評估 → 更新檔案 → ...
```

每一次學習和反饋都會更新學生的個人檔案（能力畫像、反饋摘要），從而讓下一次的 AI 交互更加個性化和精準。

## 許可證

MIT
