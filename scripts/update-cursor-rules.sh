#!/usr/bin/env bash
# ============================================================
#  自動更新 Cursor Rules 的項目快照
#  每次 git commit 前自動執行，確保 rules 與代碼同步
# ============================================================
set -e

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SNAPSHOT_FILE="$ROOT_DIR/.cursor/rules/auto-snapshot.mdc"

echo "[cursor-rules] 正在掃描項目結構，更新快照..."

# ============================================================
# 1. 收集項目文件樹
# ============================================================
FILE_TREE=$(cd "$ROOT_DIR" && find . -type f \
    \( -name "*.py" -o -name "*.ts" -o -name "*.tsx" -o -name "*.mdc" \) \
    ! -path "*/node_modules/*" ! -path "*/venv/*" ! -path "*/dist/*" ! -path "*/.git/*" \
    | sort)

FILE_COUNT=$(echo "$FILE_TREE" | wc -l | tr -d ' ')

# ============================================================
# 2. 收集後端路由摘要
# ============================================================
BACKEND_ROUTES=""
for f in "$ROOT_DIR"/backend/routers/*.py; do
    [ -f "$f" ] || continue
    fname=$(basename "$f")
    [ "$fname" = "__init__.py" ] && continue
    endpoints=$(grep -cE '^\s*@router\.(get|post|put|delete|websocket)' "$f" 2>/dev/null || echo "0")
    BACKEND_ROUTES+="  - ${fname} (${endpoints} endpoints)\n"
done

# ============================================================
# 3. 收集前端頁面摘要
# ============================================================
FRONTEND_PAGES=""
for f in "$ROOT_DIR"/frontend/src/pages/*.tsx; do
    [ -f "$f" ] || continue
    fname=$(basename "$f" .tsx)
    hooks=$(grep -oE 'use[A-Z][a-zA-Z]*' "$f" 2>/dev/null | sort -u | tr '\n' ', ' || echo "")
    FRONTEND_PAGES+="  - ${fname} [hooks: ${hooks}]\n"
done

# ============================================================
# 4. 收集數據庫模型摘要
# ============================================================
DB_MODELS=$(grep '^class.*Base' "$ROOT_DIR/backend/database/models.py" 2>/dev/null \
    | sed 's/class \([A-Za-z]*\)(Base):/  - \1/' || echo "  (none)")

# ============================================================
# 5. 收集 Pydantic Schema 摘要
# ============================================================
SCHEMAS=$(grep '^class.*BaseModel' "$ROOT_DIR/backend/schemas.py" 2>/dev/null \
    | sed 's/class \([A-Za-z]*\)(BaseModel):/  - \1/' || echo "  (none)")

# ============================================================
# 6. 收集 API 端點摘要
# ============================================================
API_ENDPOINTS=$(grep -rE '^\s*@router\.(get|post|put|delete|websocket)\(' "$ROOT_DIR/backend/routers/" 2>/dev/null \
    | sed 's|.*routers/||' | sed 's|\.py:.*@router\.||' | sed 's|(.*|)|' \
    | head -60 || echo "  (none)")

# ============================================================
# 7. 收集依賴版本
# ============================================================
PY_DEPS=$(cat "$ROOT_DIR/backend/requirements.txt" 2>/dev/null || echo "(none)")
NODE_DEPS=$(cd "$ROOT_DIR/frontend" && node -e "
const p = require('./package.json');
const deps = {...(p.dependencies||{}), ...(p.devDependencies||{})};
Object.entries(deps).forEach(([k,v]) => console.log('  ' + k + ': ' + v));
" 2>/dev/null || echo "  (none)")

# ============================================================
# 8. 生成快照文件
# ============================================================
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

cat > "$SNAPSHOT_FILE" << SNAPSHOT_EOF
---
description: 項目自動快照 (由 scripts/update-cursor-rules.sh 自動生成，勿手動編輯)
alwaysApply: true
---

# 項目自動快照
> 最後更新: ${TIMESTAMP}
> 文件總數: ${FILE_COUNT}

## 後端路由 (backend/routers/)
$(echo -e "$BACKEND_ROUTES")

## 前端頁面 (frontend/src/pages/)
$(echo -e "$FRONTEND_PAGES")

## 數據庫模型
${DB_MODELS}

## Pydantic Schemas
${SCHEMAS}

## API 端點清單
\`\`\`
${API_ENDPOINTS}
\`\`\`

## 後端依賴
\`\`\`
${PY_DEPS}
\`\`\`

## 前端依賴
\`\`\`
${NODE_DEPS}
\`\`\`

## 文件樹
\`\`\`
${FILE_TREE}
\`\`\`
SNAPSHOT_EOF

echo "[cursor-rules] 快照已更新: .cursor/rules/auto-snapshot.mdc (${TIMESTAMP})"
