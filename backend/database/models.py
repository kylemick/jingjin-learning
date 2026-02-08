from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Float, DateTime, ForeignKey, JSON, Enum
)
from sqlalchemy.orm import relationship
from database.connection import Base
import enum


# ===================== 枚舉類型 =====================

class ScenarioType(str, enum.Enum):
    ACADEMIC = "academic"       # 學科
    EXPRESSION = "expression"   # 表達
    INTERVIEW = "interview"     # 面試


class DifficultyLevel(str, enum.Enum):
    BASIC = "basic"             # 基礎
    INTERMEDIATE = "intermediate"  # 進階
    CHALLENGE = "challenge"     # 挑戰


class SubjectType(str, enum.Enum):
    CHINESE = "chinese"
    MATH = "math"
    ENGLISH = "english"
    PHYSICS = "physics"
    CHEMISTRY = "chemistry"
    BIOLOGY = "biology"
    HISTORY = "history"
    GEOGRAPHY = "geography"
    POLITICS = "politics"


class ModuleType(str, enum.Enum):
    TIME_COMPASS = "time_compass"           # 時間羅盤
    CHOICE_NAVIGATOR = "choice_navigator"   # 選擇導航
    ACTION_WORKSHOP = "action_workshop"     # 行動工坊
    LEARNING_DOJO = "learning_dojo"         # 學習道場
    THINKING_FORGE = "thinking_forge"       # 思維鍛造
    TALENT_GROWTH = "talent_growth"         # 才能精進
    REVIEW_HUB = "review_hub"              # 成長復盤


# ===================== 個人檔案系統 =====================

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    grade = Column(String(50))                    # 年級
    school = Column(String(200))                  # 學校
    target_direction = Column(String(500))        # 目標院校/方向
    personality = Column(Text)                    # 性格特點
    learning_style = Column(String(100))          # 學習風格偏好
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 關聯
    ability_profile = relationship("AbilityProfile", back_populates="student", uselist=False, cascade="all, delete-orphan")
    interests = relationship("InterestItem", back_populates="student", cascade="all, delete-orphan")
    learning_records = relationship("LearningRecord", back_populates="student", cascade="all, delete-orphan")
    feedback_summaries = relationship("FeedbackSummary", back_populates="student", cascade="all, delete-orphan")
    time_entries = relationship("TimeEntry", back_populates="student", cascade="all, delete-orphan")
    goals = relationship("Goal", back_populates="student", cascade="all, delete-orphan")
    action_plans = relationship("ActionPlan", back_populates="student", cascade="all, delete-orphan")


class AbilityProfile(Base):
    """能力畫像 - 由 AI 動態評估更新"""
    __tablename__ = "ability_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"), unique=True)

    # 學科能力 (0-100)
    chinese_score = Column(Float, default=50.0)
    math_score = Column(Float, default=50.0)
    english_score = Column(Float, default=50.0)
    physics_score = Column(Float, default=50.0)
    chemistry_score = Column(Float, default=50.0)
    biology_score = Column(Float, default=50.0)
    history_score = Column(Float, default=50.0)
    geography_score = Column(Float, default=50.0)
    politics_score = Column(Float, default=50.0)

    # 表達能力 (0-100)
    logic_score = Column(Float, default=50.0)          # 邏輯性
    language_score = Column(Float, default=50.0)        # 語言組織
    persuasion_score = Column(Float, default=50.0)      # 說服力
    creativity_score = Column(Float, default=50.0)      # 創造性

    # 面試能力 (0-100)
    confidence_score = Column(Float, default=50.0)      # 自信度
    responsiveness_score = Column(Float, default=50.0)   # 應變力
    depth_score = Column(Float, default=50.0)            # 回答深度
    uniqueness_score = Column(Float, default=50.0)       # 獨特性

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = relationship("Student", back_populates="ability_profile")


class InterestItem(Base):
    """興趣圖譜"""
    __tablename__ = "interest_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    topic = Column(String(200), nullable=False)       # 興趣主題
    depth = Column(Integer, default=1)                 # 深度 1-5
    category = Column(String(100))                     # 分類

    student = relationship("Student", back_populates="interests")


class FeedbackSummary(Base):
    """AI 累積反饋摘要"""
    __tablename__ = "feedback_summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    scenario = Column(Enum(ScenarioType))
    strengths = Column(Text)                  # 優勢摘要
    weaknesses = Column(Text)                 # 短板摘要
    progress_trend = Column(Text)             # 進步趨勢
    ai_suggestions = Column(Text)             # AI 建議
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = relationship("Student", back_populates="feedback_summaries")


# ===================== 題庫系統 =====================

class Question(Base):
    """題庫"""
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scenario = Column(Enum(ScenarioType), nullable=False)
    difficulty = Column(Enum(DifficultyLevel), default=DifficultyLevel.BASIC)
    subject = Column(Enum(SubjectType), nullable=True)     # 學科場景時使用
    question_type = Column(String(50))                      # 題目類型
    title = Column(Text, nullable=False)                    # 題幹
    options = Column(JSON, nullable=True)                   # 選項 (選擇題)
    reference_answer = Column(Text)                         # 參考答案
    knowledge_tags = Column(JSON)                           # 知識點標籤
    solution_hint = Column(Text)                            # 解題思路
    scoring_dimensions = Column(JSON)                       # 評分維度
    created_at = Column(DateTime, default=datetime.utcnow)
    is_ai_generated = Column(Integer, default=0)            # 是否 AI 生成


# ===================== 七大模組數據 =====================

class TimeEntry(Base):
    """時間羅盤 - 時間投入記錄"""
    __tablename__ = "time_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    activity = Column(String(500), nullable=False)
    duration_minutes = Column(Integer)
    half_life = Column(String(20))                # long / short
    benefit_value = Column(Integer)               # 收益值 1-5
    date = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="time_entries")


class Goal(Base):
    """選擇導航 - 目標管理"""
    __tablename__ = "goals"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    scenario = Column(Enum(ScenarioType))
    title = Column(String(500), nullable=False)
    description = Column(Text)
    five_year_vision = Column(Text)               # 五年後願景
    hidden_assumptions = Column(Text)             # 識別出的隱含假設
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="goals")


class ActionPlan(Base):
    """行動工坊 - 行動計劃"""
    __tablename__ = "action_plans"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    goal_id = Column(Integer, ForeignKey("goals.id"), nullable=True)
    title = Column(String(500), nullable=False)
    core_tasks = Column(JSON)                     # 核心區間任務
    support_tasks = Column(JSON)                  # 支撐區間任務
    status = Column(String(50), default="pending")
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    student = relationship("Student", back_populates="action_plans")


class LearningRecord(Base):
    """學習歷程記錄"""
    __tablename__ = "learning_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    module = Column(Enum(ModuleType), nullable=False)
    scenario = Column(Enum(ScenarioType))
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=True)
    content = Column(Text)                        # 學生的回答/練習內容
    ai_feedback = Column(Text)                    # AI 反饋
    score = Column(Float, nullable=True)          # 得分
    reflection = Column(Text)                     # 學生的反思 (三行而後思)
    duration_minutes = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("Student", back_populates="learning_records")
