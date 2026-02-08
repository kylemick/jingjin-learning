#!/usr/bin/env python3
"""
繁體中文一鍵檢查腳本
功能：
  1. 掃描 MySQL 數據庫所有文本欄位，檢測簡體字
  2. 掃描前端 .tsx/.ts 文件中的中文字串常量，檢測簡體字
  3. 加 --fix 參數可自動修正數據庫中的簡體字（前端只報告位置）

用法：
  python scripts/check-traditional-chinese.py          # 僅檢測
  python scripts/check-traditional-chinese.py --fix    # 檢測並修正數據庫
"""
import argparse
import os
import re
import sys

# 將 backend 加入 path，以便引用項目模組
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from opencc import OpenCC

_s2t = OpenCC("s2t")

# ─── 中文檢測工具 ───

def has_simplified(text: str) -> bool:
    """檢測文本是否包含簡體字"""
    if not text:
        return False
    return _s2t.convert(text) != text


def to_traditional(text: str) -> str:
    """簡體 → 繁體"""
    return _s2t.convert(text) if text else text


def diff_chars(original: str, converted: str) -> list[tuple[int, str, str]]:
    """找出所有不同的字元位置"""
    diffs = []
    for i, (o, c) in enumerate(zip(original, converted)):
        if o != c:
            diffs.append((i, o, c))
    return diffs


# ─── 數據庫掃描 ───

# 需要掃描的表及其文本欄位
TABLE_TEXT_COLUMNS = {
    "students": ["name", "grade", "school", "target_direction", "personality", "learning_style"],
    "interest_items": ["topic", "category"],
    "feedback_summaries": ["strengths", "weaknesses", "progress_trend", "ai_suggestions"],
    "questions": ["title", "reference_answer", "solution_hint", "question_type"],
    "time_entries": ["activity"],
    "goals": ["title", "description", "five_year_vision", "hidden_assumptions", "status"],
    "action_plans": ["title", "status"],
    "learning_records": ["content", "ai_feedback", "reflection"],
    "conversations": ["title"],
    "chat_messages": ["content", "role", "phase_at_time"],
}


def scan_database(fix: bool = False):
    """掃描數據庫中的簡體字"""
    import pymysql
    from dotenv import dotenv_values

    env_path = os.path.join(os.path.dirname(__file__), "..", "backend", ".env")
    env = dotenv_values(env_path)

    conn_params = {
        "host": env.get("MYSQL_HOST", "localhost"),
        "port": int(env.get("MYSQL_PORT", "3306")),
        "user": env.get("MYSQL_USER", "root"),
        "password": env.get("MYSQL_PASSWORD", ""),
        "database": env.get("MYSQL_DATABASE", "jingjin"),
        "charset": "utf8mb4",
    }

    print("\n" + "=" * 60)
    print("📊 數據庫簡體字掃描")
    print("=" * 60)

    try:
        conn = pymysql.connect(**conn_params)
    except Exception as e:
        print(f"  ❌ 無法連接數據庫: {e}")
        return 0

    cursor = conn.cursor()
    total_issues = 0
    total_fixed = 0

    # 先檢查哪些表存在
    cursor.execute("SHOW TABLES")
    existing_tables = {row[0] for row in cursor.fetchall()}

    for table, columns in TABLE_TEXT_COLUMNS.items():
        if table not in existing_tables:
            continue

        # 檢查表中哪些欄位存在
        cursor.execute(f"DESCRIBE `{table}`")
        existing_cols = {row[0] for row in cursor.fetchall()}
        valid_cols = [c for c in columns if c in existing_cols]
        if not valid_cols:
            continue

        col_list = ", ".join(f"`{c}`" for c in valid_cols)
        cursor.execute(f"SELECT id, {col_list} FROM `{table}`")
        rows = cursor.fetchall()

        table_issues = 0
        for row in rows:
            row_id = row[0]
            for idx, col_name in enumerate(valid_cols):
                value = row[idx + 1]
                if not value or not isinstance(value, str):
                    continue
                if has_simplified(value):
                    converted = to_traditional(value)
                    diffs = diff_chars(value, converted)
                    diff_sample = ", ".join(f"'{o}'→'{c}'" for _, o, c in diffs[:5])
                    if len(diffs) > 5:
                        diff_sample += f" ...等 {len(diffs)} 處"

                    print(f"\n  ⚠️  {table}.{col_name} (id={row_id})")
                    print(f"     簡體字: {diff_sample}")
                    preview = value[:80].replace("\n", "\\n")
                    print(f"     內容預覽: {preview}...")

                    total_issues += 1
                    table_issues += 1

                    if fix:
                        cursor.execute(
                            f"UPDATE `{table}` SET `{col_name}` = %s WHERE id = %s",
                            (converted, row_id),
                        )
                        total_fixed += 1
                        print(f"     ✅ 已修正")

        if table_issues == 0 and table in existing_tables:
            pass  # 只在有問題時輸出

    if fix:
        conn.commit()
    cursor.close()
    conn.close()

    if total_issues == 0:
        print("\n  ✅ 數據庫中未發現簡體字，全部為繁體中文！")
    else:
        print(f"\n  共發現 {total_issues} 處簡體字")
        if fix:
            print(f"  已自動修正 {total_fixed} 處")
        else:
            print("  使用 --fix 參數可自動修正數據庫中的簡體字")

    return total_issues


# ─── 前端文件掃描 ───

# 匹配中文字串：單引號、雙引號、反引號中的中文
CHINESE_PATTERN = re.compile(r"""[\u4e00-\u9fff]+""")

# 匹配字串常量中的中文
STRING_PATTERNS = [
    re.compile(r"'([^']*[\u4e00-\u9fff][^']*)'"),      # 單引號字串
    re.compile(r'"([^"]*[\u4e00-\u9fff][^"]*)"'),       # 雙引號字串
    re.compile(r'`([^`]*[\u4e00-\u9fff][^`]*)`'),       # 模板字串
]


def scan_frontend():
    """掃描前端文件中的簡體字"""
    frontend_src = os.path.join(os.path.dirname(__file__), "..", "frontend", "src")

    print("\n" + "=" * 60)
    print("📝 前端文件簡體字掃描")
    print("=" * 60)

    if not os.path.exists(frontend_src):
        print("  ❌ 前端 src 目錄不存在")
        return 0

    total_issues = 0

    for root, dirs, files in os.walk(frontend_src):
        for fname in sorted(files):
            if not fname.endswith((".tsx", ".ts")):
                continue

            filepath = os.path.join(root, fname)
            rel_path = os.path.relpath(filepath, os.path.join(os.path.dirname(__file__), ".."))

            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    lines = f.readlines()
            except Exception:
                continue

            file_issues = []
            for line_num, line in enumerate(lines, 1):
                for pattern in STRING_PATTERNS:
                    for match in pattern.finditer(line):
                        chinese_text = match.group(1)
                        if has_simplified(chinese_text):
                            converted = to_traditional(chinese_text)
                            diffs = diff_chars(chinese_text, converted)
                            diff_sample = ", ".join(f"'{o}'→'{c}'" for _, o, c in diffs[:3])
                            file_issues.append((line_num, chinese_text[:50], diff_sample))

            if file_issues:
                print(f"\n  📄 {rel_path}")
                for line_num, text, diff in file_issues:
                    print(f"     行 {line_num}: \"{text}\" — {diff}")
                    total_issues += 1

    if total_issues == 0:
        print("\n  ✅ 前端文件中未發現簡體字，全部為繁體中文！")
    else:
        print(f"\n  共發現 {total_issues} 處簡體字")
        print("  請手動修改前端源碼中的簡體字")

    return total_issues


# ─── 主入口 ───

def main():
    parser = argparse.ArgumentParser(description="檢查並修正系統中的簡體字")
    parser.add_argument(
        "--fix",
        action="store_true",
        help="自動修正數據庫中的簡體字（前端文件僅報告，不自動修改）",
    )
    parser.add_argument(
        "--db-only",
        action="store_true",
        help="僅掃描數據庫",
    )
    parser.add_argument(
        "--frontend-only",
        action="store_true",
        help="僅掃描前端文件",
    )
    args = parser.parse_args()

    print("🔍 繁體中文合規檢查工具")
    print("   確保系統所有中文輸出均為繁體中文（正體中文）")

    db_issues = 0
    fe_issues = 0

    if not args.frontend_only:
        db_issues = scan_database(fix=args.fix)

    if not args.db_only:
        fe_issues = scan_frontend()

    # 總結
    total = db_issues + fe_issues
    print("\n" + "=" * 60)
    print("📋 檢查總結")
    print("=" * 60)
    if total == 0:
        print("  ✅ 全部通過！系統中未發現簡體字。")
    else:
        print(f"  ⚠️  共發現 {total} 處簡體字（數據庫: {db_issues}, 前端: {fe_issues}）")
        if not args.fix:
            print("  💡 使用 --fix 參數可自動修正數據庫中的簡體字")

    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
