#!/usr/bin/env bash
# ============================================================
#  精進學習系統 - 一鍵啟動腳本
#  功能：
#    1. 檢查 MySQL 是否運行
#    2. 自動建立數據庫（如不存在），不覆蓋已有數據
#    3. 自動安裝依賴（如需要）
#    4. 同時啟動前後端，日誌統一輸出到 console
# ============================================================
set -e

ROOT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
LOG_DIR="$ROOT_DIR/.logs"
mkdir -p "$LOG_DIR"

# 顏色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ============================================================
# 進程清理（使用進程組確保完整清理）
# ============================================================
BACKEND_PID=""
FRONTEND_PID=""
TAIL_PID=""

cleanup() {
    echo ""
    echo -e "${YELLOW}正在停止所有服務...${NC}"

    # 停止 tail
    [ -n "$TAIL_PID" ] && kill "$TAIL_PID" 2>/dev/null

    # 停止後端 (uvicorn)
    if [ -n "$BACKEND_PID" ]; then
        kill "$BACKEND_PID" 2>/dev/null
        wait "$BACKEND_PID" 2>/dev/null
    fi

    # 停止前端 (vite)
    if [ -n "$FRONTEND_PID" ]; then
        kill "$FRONTEND_PID" 2>/dev/null
        wait "$FRONTEND_PID" 2>/dev/null
    fi

    # 確保 8000 和 5173 端口已釋放
    lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null || true
    lsof -ti:5173 2>/dev/null | xargs kill -9 2>/dev/null || true

    echo -e "${GREEN}所有服務已停止。再見！${NC}"
    exit 0
}

trap cleanup SIGINT SIGTERM EXIT

# 先清理可能殘留的舊進程
lsof -ti:8000 2>/dev/null | xargs kill -9 2>/dev/null || true
lsof -ti:5173 2>/dev/null | xargs kill -9 2>/dev/null || true
sleep 1

echo -e "${BOLD}${CYAN}"
echo "  ╔═══════════════════════════════════════════╗"
echo "  ║       精進學習系統 · 一鍵啟動腳本         ║"
echo "  ║  《精進：如何成為一個很厲害的人》         ║"
echo "  ╚═══════════════════════════════════════════╝"
echo -e "${NC}"

# ============================================================
# 1. 讀取配置
# ============================================================
if [ ! -f "$BACKEND_DIR/.env" ]; then
    echo -e "${RED}✗ 找不到 backend/.env 配置文件${NC}"
    echo "  請先複製 .env.example 並填入配置："
    echo "  cp backend/.env.example backend/.env"
    exit 1
fi

MYSQL_USER=$(grep '^MYSQL_USER=' "$BACKEND_DIR/.env" | cut -d'=' -f2)
MYSQL_PASSWORD=$(grep '^MYSQL_PASSWORD=' "$BACKEND_DIR/.env" | cut -d'=' -f2)
MYSQL_HOST=$(grep '^MYSQL_HOST=' "$BACKEND_DIR/.env" | cut -d'=' -f2)
MYSQL_PORT=$(grep '^MYSQL_PORT=' "$BACKEND_DIR/.env" | cut -d'=' -f2)
MYSQL_DATABASE=$(grep '^MYSQL_DATABASE=' "$BACKEND_DIR/.env" | cut -d'=' -f2)

MYSQL_USER=${MYSQL_USER:-root}
MYSQL_HOST=${MYSQL_HOST:-localhost}
MYSQL_PORT=${MYSQL_PORT:-3306}
MYSQL_DATABASE=${MYSQL_DATABASE:-jingjin}

echo -e "${CYAN}[配置]${NC} MySQL: ${MYSQL_USER}@${MYSQL_HOST}:${MYSQL_PORT}/${MYSQL_DATABASE}"

# ============================================================
# 2. 檢查 MySQL
# ============================================================
echo -e "\n${BOLD}[1/5] 檢查 MySQL ...${NC}"

if ! command -v mysql &>/dev/null; then
    echo -e "${RED}✗ 未找到 mysql 命令，請先安裝 MySQL${NC}"
    exit 1
fi

MYSQL_CMD="mysql -u${MYSQL_USER} -h${MYSQL_HOST} -P${MYSQL_PORT}"
if [ -n "$MYSQL_PASSWORD" ]; then
    MYSQL_CMD="$MYSQL_CMD -p${MYSQL_PASSWORD}"
fi

if ! $MYSQL_CMD -e "SELECT 1" &>/dev/null; then
    echo -e "${RED}✗ 無法連接 MySQL，請確認：${NC}"
    echo "  1. MySQL 服務是否運行 (brew services start mysql)"
    echo "  2. backend/.env 中的密碼是否正確"
    exit 1
fi
echo -e "${GREEN}✓ MySQL 連接成功${NC}"

DB_EXISTS=$($MYSQL_CMD -N -e "SELECT SCHEMA_NAME FROM information_schema.SCHEMATA WHERE SCHEMA_NAME='${MYSQL_DATABASE}';" 2>/dev/null)
if [ -z "$DB_EXISTS" ]; then
    echo -e "${YELLOW}  數據庫 ${MYSQL_DATABASE} 不存在，正在建立...${NC}"
    $MYSQL_CMD -e "CREATE DATABASE ${MYSQL_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;" 2>/dev/null
    echo -e "${GREEN}  ✓ 數據庫 ${MYSQL_DATABASE} 建立成功${NC}"
else
    TABLE_COUNT=$($MYSQL_CMD -N -e "SELECT COUNT(*) FROM information_schema.TABLES WHERE TABLE_SCHEMA='${MYSQL_DATABASE}';" 2>/dev/null)
    echo -e "${GREEN}✓ 數據庫 ${MYSQL_DATABASE} 已存在 (${TABLE_COUNT} 個表)，數據將完整保留${NC}"
fi

# ============================================================
# 3. 初始化後端
# ============================================================
echo -e "\n${BOLD}[2/5] 初始化後端環境 ...${NC}"

if [ ! -d "$BACKEND_DIR/venv" ]; then
    echo -e "${YELLOW}  建立 Python 虛擬環境...${NC}"
    python3 -m venv "$BACKEND_DIR/venv"
fi

source "$BACKEND_DIR/venv/bin/activate"

if ! python -c "import fastapi" &>/dev/null; then
    echo -e "${YELLOW}  安裝 Python 依賴...${NC}"
    pip install -r "$BACKEND_DIR/requirements.txt" -q
fi
echo -e "${GREEN}✓ 後端環境就緒${NC}"

# ============================================================
# 4. 初始化前端
# ============================================================
echo -e "\n${BOLD}[3/5] 初始化前端環境 ...${NC}"

if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo -e "${YELLOW}  安裝 npm 依賴...${NC}"
    (cd "$FRONTEND_DIR" && npm install -q)
fi
echo -e "${GREEN}✓ 前端環境就緒${NC}"

# ============================================================
# 5. 啟動後端（直接啟動，不用管道，日誌寫文件）
# ============================================================
echo -e "\n${BOLD}[4/5] 啟動後端服務 (port 8000) ...${NC}"

# 清空舊日誌
> "$LOG_DIR/backend.log"
> "$LOG_DIR/frontend.log"

(
    cd "$BACKEND_DIR"
    source venv/bin/activate
    exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload --log-level info \
        >> "$LOG_DIR/backend.log" 2>&1
) &
BACKEND_PID=$!

# 等待後端就緒
echo -n "  等待後端啟動"
BACKEND_READY=false
for i in $(seq 1 30); do
    if curl -s http://localhost:8000/api/health &>/dev/null; then
        echo ""
        echo -e "${GREEN}✓ 後端已就緒 (PID: $BACKEND_PID)${NC}"
        BACKEND_READY=true
        break
    fi
    # 檢查進程是否還活著
    if ! kill -0 "$BACKEND_PID" 2>/dev/null; then
        echo ""
        echo -e "${RED}✗ 後端啟動失敗！最後日誌：${NC}"
        tail -20 "$LOG_DIR/backend.log"
        exit 1
    fi
    echo -n "."
    sleep 1
done

if [ "$BACKEND_READY" != "true" ]; then
    echo ""
    echo -e "${RED}✗ 後端啟動超時！最後日誌：${NC}"
    tail -20 "$LOG_DIR/backend.log"
    exit 1
fi

# ============================================================
# 6. 啟動前端
# ============================================================
echo -e "\n${BOLD}[5/5] 啟動前端服務 (port 5173) ...${NC}"

(
    cd "$FRONTEND_DIR"
    exec npx vite --host >> "$LOG_DIR/frontend.log" 2>&1
) &
FRONTEND_PID=$!

# 等待前端就緒
echo -n "  等待前端啟動"
for i in $(seq 1 15); do
    if curl -s http://localhost:5173 &>/dev/null; then
        echo ""
        echo -e "${GREEN}✓ 前端已就緒 (PID: $FRONTEND_PID)${NC}"
        break
    fi
    if ! kill -0 "$FRONTEND_PID" 2>/dev/null; then
        echo ""
        echo -e "${RED}✗ 前端啟動失敗！最後日誌：${NC}"
        tail -20 "$LOG_DIR/frontend.log"
        exit 1
    fi
    echo -n "."
    sleep 1
done

echo ""
echo -e "${BOLD}${GREEN}"
echo "  ╔═══════════════════════════════════════════╗"
echo "  ║          精進學習系統 · 啟動完成!          ║"
echo "  ╠═══════════════════════════════════════════╣"
echo "  ║  前端:  http://localhost:5173             ║"
echo "  ║  後端:  http://localhost:8000             ║"
echo "  ║  文檔:  http://localhost:8000/docs        ║"
echo "  ╠═══════════════════════════════════════════╣"
echo "  ║  按 Ctrl+C 停止所有服務                    ║"
echo "  ╚═══════════════════════════════════════════╝"
echo -e "${NC}"

# ============================================================
# 7. 合併日誌實時輸出到 console
# ============================================================
tail -f "$LOG_DIR/backend.log" "$LOG_DIR/frontend.log" 2>/dev/null \
    | awk '
        /^==> .*backend\.log/ { prefix="\033[0;36m[後端]\033[0m "; next }
        /^==> .*frontend\.log/ { prefix="\033[1;33m[前端]\033[0m "; next }
        /^$/  { next }
        { print prefix $0; fflush() }
    ' &
TAIL_PID=$!

# 持續運行，等待子進程結束或 Ctrl+C
wait $BACKEND_PID $FRONTEND_PID 2>/dev/null
