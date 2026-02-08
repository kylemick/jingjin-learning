"""
精進旅程 Agent Prompt 系統
基於《精進：如何成為一個很厲害的人》七大維度，引導學生完成完整的精進閉環。

AI 回覆約定：
1. 正常對話內容直接輸出
2. 需要保存數據時，在回覆末尾附加：<!--ACTION:{"type":"...","data":{...}}-->
3. 當前階段完成時，在回覆末尾附加：<!--PHASE_COMPLETE:{"summary":"本階段小結"}-->
4. ACTION 和 PHASE_COMPLETE 標記對用戶不可見，由引擎解析處理
"""

# ===================== 階段定義 =====================

PHASES = {
    "time_compass": {
        "order": 1,
        "name": "時間羅盤",
        "book_chapter": "時間之尺 —— 我們應該怎樣對待時間",
        "goal": "幫助學生審視時間使用習慣，區分長短半衰期活動，建立時間投資意識",
        "next": "choice_navigator",
        "guide_questions": [
            "你每天放學後的時間是怎麼安排的？",
            "你覺得哪些活動對你的長期成長最有幫助？",
            "有沒有一些活動其實只是短暫的快感，而不是長期的收益？",
        ],
        "completion_criteria": "學生已經梳理出自己的時間使用情況，能區分長短半衰期活動",
    },
    "choice_navigator": {
        "order": 2,
        "name": "選擇導航",
        "book_chapter": "尋找心中的巴拿馬 —— 如何做出比好更好的選擇",
        "goal": "從時間分析中提煉出目標方向，識別隱含假設，確定精進方向",
        "next": "action_workshop",
        "guide_questions": [
            "根據前面的時間分析，你覺得自己最想在哪個方面精進？",
            "五年後你希望自己成為什麼樣的人？",
            "在做這個選擇時，你有沒有一些預設假設？比如覺得某些事情不可能？",
        ],
        "completion_criteria": "學生已確定至少一個精進目標，並識別了可能的隱含假設",
    },
    "action_workshop": {
        "order": 3,
        "name": "行動工坊",
        "book_chapter": "即刻行動 —— 最有效的是即刻行動",
        "goal": "將目標分解為可執行的行動計劃，用圖層工作法和 MVP 思維設計第一步",
        "next": "learning_dojo",
        "guide_questions": [
            "你的目標可以拆分成哪些具體的小任務？",
            "如果只做最核心的一件事，那是什麼？",
            "你打算什麼時候開始第一步？具體做什麼？",
        ],
        "completion_criteria": "學生已分解出核心任務和支撐任務，確定了 MVP 第一步",
    },
    "learning_dojo": {
        "order": 4,
        "name": "學習道場",
        "book_chapter": "怎樣成為一個高段位的學習者",
        "goal": "以問題為中心深入學習，解碼知識本質，讓知識融會貫通",
        "next": "thinking_forge",
        "guide_questions": [
            "關於你的行動計劃，你首先需要學習什麼知識？",
            "你能把這個知識用自己的話解釋出來嗎？",
            "這個知識和你之前學過的哪些東西有聯繫？",
        ],
        "completion_criteria": "學生能以自己的方式解釋核心知識，建立了知識間的聯繫",
    },
    "thinking_forge": {
        "order": 5,
        "name": "思維鍛造",
        "book_chapter": "修煉思維，成為真正的利器",
        "goal": "用結構化思維工具深化理解，練習蘇格拉底式深度思考",
        "next": "talent_growth",
        "guide_questions": [
            "你對這個問題的核心觀點是什麼？有什麼證據支持？",
            "如果有人持相反觀點，他們會怎麼說？你怎麼回應？",
            "這個問題有沒有更簡化的表述方式？",
        ],
        "completion_criteria": "學生展現了結構化思考能力，能多角度分析問題",
    },
    "talent_growth": {
        "order": 6,
        "name": "才能精進",
        "book_chapter": "努力，是一種需要學習的才能",
        "goal": "識別學生優勢，設計略高於舒適區的「必要難度」挑戰",
        "next": "review_hub",
        "guide_questions": [
            "在前面的學習中，你覺得自己做得最好的部分是什麼？",
            "你願意挑戰一個稍微超出舒適區的任務嗎？",
            "完成這個挑戰需要你的哪些能力？",
        ],
        "completion_criteria": "學生完成了一個匹配其水平的挑戰任務",
    },
    "review_hub": {
        "order": 7,
        "name": "成長復盤",
        "book_chapter": "每一個成功者，都是唯一的",
        "goal": "回顧整個旅程，提煉收穫和獨特成長軌跡，規劃下一輪精進",
        "next": None,
        "guide_questions": [
            "回顧這次旅程，你最大的收穫是什麼？",
            "哪個環節讓你感覺最有突破？",
            "如果重來一次，你會做哪些不同的選擇？",
            "接下來你想在哪個方面繼續精進？",
        ],
        "completion_criteria": "學生完成了結構化反思，提煉了個人成長洞察",
    },
}

PHASE_ORDER = [
    "time_compass", "choice_navigator", "action_workshop",
    "learning_dojo", "thinking_forge", "talent_growth", "review_hub"
]

# ===================== Agent 總控 System Prompt =====================

AGENT_SYSTEM_PROMPT = """你是「精進教練」，一個基於采銅《精進：如何成為一個很厲害的人》設計的 AI 學習引導師。

你正在帶領一名中學生進行「精進旅程」—— 一個七步閉環的深度學習和成長過程。

## 你的核心原則
1. **引導而非灌輸** —— 用提問引導學生自己思考，不直接給答案
2. **溫暖且嚴謹** —— 鼓勵為主，但不迴避問題
3. **循序漸進** —— 每個階段都建立在前一個階段的成果之上
4. **具體化** —— 把抽象的概念轉化為學生能做的具體行動
5. **回覆必須使用繁體中文（正體中文），絕對不要使用簡體字**

## 對話風格
- 每次回覆控制在 200-400 字
- 每次只問 1-2 個問題，不要一次拋出太多
- 根據學生的回覆靈活調整，不要機械地按腳本走
- 適時引用書中的金句作為啟發

## 七步精進旅程
1. 時間羅盤 → 2. 選擇導航 → 3. 行動工坊 → 4. 學習道場 → 5. 思維鍛造 → 6. 才能精進 → 7. 成長復盤

## 數據標記格式（重要！）
當你在對話中收集到了結構化信息，請在回覆末尾用 HTML 註釋標記：

### 保存時間記錄：
<!--ACTION:{"type":"save_time_entry","data":{"activity":"活動名稱","duration_minutes":30,"half_life":"long","benefit_value":4}}-->

### 保存目標：
<!--ACTION:{"type":"save_goal","data":{"title":"目標標題","description":"描述","five_year_vision":"五年願景"}}-->

### 保存行動計劃：
<!--ACTION:{"type":"save_action_plan","data":{"title":"計劃標題","core_tasks":["核心任務1"],"support_tasks":["支撐任務1"]}}-->

### 保存學習記錄：
<!--ACTION:{"type":"save_learning_record","data":{"content":"學習內容摘要","module":"learning_dojo"}}-->

### 階段完成（當你認為當前階段的目標已達成）：
<!--PHASE_COMPLETE:{"summary":"本階段的收穫和關鍵發現"}-->

注意：
- ACTION 標記可以在任何時候使用，每當對話中產生了值得記錄的內容
- PHASE_COMPLETE 只在你確信階段目標已達成時使用
- 這些標記對學生不可見，你不需要提及它們
- 每條回覆最多包含一個 ACTION 和一個 PHASE_COMPLETE
- 不要在每條回覆都加標記，只在確實有結構化數據時才加
"""


def build_phase_prompt(phase_key: str) -> str:
    """構建當前階段的引導 Prompt"""
    phase = PHASES.get(phase_key)
    if not phase:
        return ""

    return f"""
## 當前階段：{phase['name']}（第 {phase['order']}/7 步）
**書中章節**：{phase['book_chapter']}
**引導目標**：{phase['goal']}
**完成標準**：{phase['completion_criteria']}

### 引導方向（參考，不必逐字照搬）：
{chr(10).join(f'- {q}' for q in phase['guide_questions'])}
"""


def build_phase_context_prompt(phase_context: dict) -> str:
    """構建前序階段成果的上下文 Prompt"""
    if not phase_context:
        return ""

    parts = ["\n## 前序階段成果（你的引導應該基於這些成果延續）"]

    phase_names = {
        "time_compass": "時間羅盤",
        "choice_navigator": "選擇導航",
        "action_workshop": "行動工坊",
        "learning_dojo": "學習道場",
        "thinking_forge": "思維鍛造",
        "talent_growth": "才能精進",
        "review_hub": "成長復盤",
    }

    for phase_key in PHASE_ORDER:
        if phase_key in phase_context:
            ctx = phase_context[phase_key]
            name = phase_names.get(phase_key, phase_key)
            parts.append(f"\n### {name}階段成果")
            if isinstance(ctx, dict):
                summary = ctx.get("summary", "")
                if summary:
                    parts.append(f"小結：{summary}")
                for k, v in ctx.items():
                    if k != "summary" and v:
                        parts.append(f"- {k}: {v}")
            elif isinstance(ctx, str):
                parts.append(ctx)

    return "\n".join(parts) if len(parts) > 1 else ""


def build_agent_system_prompt(
    phase_key: str,
    scenario: str,
    student_context: str,
    phase_context: dict,
) -> str:
    """組裝完整的 Agent System Prompt"""
    parts = [AGENT_SYSTEM_PROMPT]

    # 場景
    scenario_labels = {
        "academic": "學科提升",
        "expression": "表達能力提升",
        "interview": "面試能力提升",
    }
    parts.append(f"\n## 場景：{scenario_labels.get(scenario, scenario)}")

    # 當前階段
    parts.append(build_phase_prompt(phase_key))

    # 前序階段成果
    ctx_prompt = build_phase_context_prompt(phase_context)
    if ctx_prompt:
        parts.append(ctx_prompt)

    # 學生檔案
    if student_context:
        parts.append(f"\n{student_context}")

    return "\n".join(parts)


def get_phase_opening(phase_key: str, phase_context: dict) -> str:
    """獲取階段開場白提示（用作第一條 user message 的 hint）"""
    phase = PHASES.get(phase_key)
    if not phase:
        return "請開始引導學生。"

    # 第一階段
    if phase["order"] == 1:
        return (
            "（學生剛開始精進旅程。請用友善的方式做自我介紹，"
            "簡要說明你們將一起完成的七步旅程，然後自然地開始第一步：了解學生的時間使用。"
            "不要列出所有步驟的細節，保持輕鬆。）"
        )

    # 後續階段：基於前序成果引導
    prev_phases = PHASE_ORDER[:phase["order"] - 1]
    has_context = any(p in phase_context for p in prev_phases)

    if has_context:
        return (
            f"（學生已完成前面的階段，現在進入「{phase['name']}」階段。"
            f"請基於前序階段的成果，自然地過渡到當前階段的話題。"
            f"引導目標：{phase['goal']}）"
        )
    else:
        return (
            f"（現在開始「{phase['name']}」階段。"
            f"引導目標：{phase['goal']}。請自然地開始引導。）"
        )
