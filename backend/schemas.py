from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


# ===================== 學生 / 個人檔案 =====================

class StudentCreate(BaseModel):
    name: str
    grade: Optional[str] = None
    school: Optional[str] = None
    target_direction: Optional[str] = None
    personality: Optional[str] = None
    learning_style: Optional[str] = None


class StudentUpdate(BaseModel):
    name: Optional[str] = None
    grade: Optional[str] = None
    school: Optional[str] = None
    target_direction: Optional[str] = None
    personality: Optional[str] = None
    learning_style: Optional[str] = None


class AbilityProfileOut(BaseModel):
    chinese_score: float = 50.0
    math_score: float = 50.0
    english_score: float = 50.0
    physics_score: float = 50.0
    chemistry_score: float = 50.0
    biology_score: float = 50.0
    history_score: float = 50.0
    geography_score: float = 50.0
    politics_score: float = 50.0
    logic_score: float = 50.0
    language_score: float = 50.0
    persuasion_score: float = 50.0
    creativity_score: float = 50.0
    confidence_score: float = 50.0
    responsiveness_score: float = 50.0
    depth_score: float = 50.0
    uniqueness_score: float = 50.0

    class Config:
        from_attributes = True


class InterestItemOut(BaseModel):
    id: int
    topic: str
    depth: int
    category: Optional[str] = None

    class Config:
        from_attributes = True


class StudentOut(BaseModel):
    id: int
    name: str
    grade: Optional[str] = None
    school: Optional[str] = None
    target_direction: Optional[str] = None
    personality: Optional[str] = None
    learning_style: Optional[str] = None
    ability_profile: Optional[AbilityProfileOut] = None
    interests: List[InterestItemOut] = []
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===================== 興趣 =====================

class InterestCreate(BaseModel):
    topic: str
    depth: int = 1
    category: Optional[str] = None


# ===================== 題庫 =====================

class QuestionCreate(BaseModel):
    scenario: str
    difficulty: str = "basic"
    subject: Optional[str] = None
    question_type: Optional[str] = None
    title: str
    options: Optional[list] = None
    reference_answer: Optional[str] = None
    knowledge_tags: Optional[list] = None
    solution_hint: Optional[str] = None
    scoring_dimensions: Optional[list] = None


class QuestionOut(BaseModel):
    id: int
    scenario: str
    difficulty: str
    subject: Optional[str] = None
    question_type: Optional[str] = None
    title: str
    options: Optional[list] = None
    reference_answer: Optional[str] = None
    knowledge_tags: Optional[list] = None
    solution_hint: Optional[str] = None
    scoring_dimensions: Optional[list] = None

    class Config:
        from_attributes = True


# ===================== 時間羅盤 =====================

class TimeEntryCreate(BaseModel):
    activity: str
    duration_minutes: int
    half_life: str = "long"     # long / short
    benefit_value: int = 3      # 1-5


class TimeEntryOut(BaseModel):
    id: int
    activity: str
    duration_minutes: int
    half_life: str
    benefit_value: int
    date: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===================== 目標 / 選擇導航 =====================

class GoalCreate(BaseModel):
    scenario: str
    title: str
    description: Optional[str] = None
    five_year_vision: Optional[str] = None


class GoalOut(BaseModel):
    id: int
    scenario: str
    title: str
    description: Optional[str] = None
    five_year_vision: Optional[str] = None
    hidden_assumptions: Optional[str] = None
    status: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===================== 行動計劃 =====================

class ActionPlanCreate(BaseModel):
    goal_id: Optional[int] = None
    title: str
    core_tasks: Optional[list] = None
    support_tasks: Optional[list] = None


class ActionPlanOut(BaseModel):
    id: int
    title: str
    goal_id: Optional[int] = None
    core_tasks: Optional[list] = None
    support_tasks: Optional[list] = None
    status: str
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===================== 學習記錄 =====================

class LearningRecordCreate(BaseModel):
    module: str
    scenario: Optional[str] = None
    question_id: Optional[int] = None
    content: Optional[str] = None
    duration_minutes: Optional[int] = None


class LearningRecordOut(BaseModel):
    id: int
    module: str
    scenario: Optional[str] = None
    question_id: Optional[int] = None
    content: Optional[str] = None
    ai_feedback: Optional[str] = None
    score: Optional[float] = None
    reflection: Optional[str] = None
    duration_minutes: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ===================== AI 交互 =====================

class AIRequest(BaseModel):
    module: str                          # 模組類型
    scenario: Optional[str] = None       # 場景
    student_id: int
    message: str                         # 用戶消息
    question_id: Optional[int] = None    # 關聯題目


class ReflectionCreate(BaseModel):
    record_id: int
    reflection: str


class FeedbackSummaryOut(BaseModel):
    id: int
    scenario: str
    strengths: Optional[str] = None
    weaknesses: Optional[str] = None
    progress_trend: Optional[str] = None
    ai_suggestions: Optional[str] = None

    class Config:
        from_attributes = True


# ===================== Agent 對話 =====================

class ConversationCreate(BaseModel):
    title: Optional[str] = "新的精進旅程"
    scenario: str = "academic"

class ChatMessageOut(BaseModel):
    id: int
    role: str
    content: str
    phase_at_time: Optional[str] = None
    action_metadata: Optional[dict] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ConversationOut(BaseModel):
    id: int
    title: str
    scenario: str
    current_phase: str
    phase_context: Optional[dict] = None
    status: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ConversationDetailOut(ConversationOut):
    messages: List[ChatMessageOut] = []

class AgentChatRequest(BaseModel):
    message: str
