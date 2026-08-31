from typing import List

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import Boolean, Column, Float, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(title="Nova Digital Literacy Hub")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# DATABASE
# ============================================================

SQLALCHEMY_DATABASE_URL = "sqlite:///./nova_hub.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


# ============================================================
# DATABASE MODELS
# ============================================================

class LearnerDB(Base):
    """Database table for learners."""

    __tablename__ = "learners"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)


class QuizResultDB(Base):
    """Database table for quiz results."""

    __tablename__ = "quiz_results"

    id = Column(Integer, primary_key=True, index=True)
    learner_id = Column(Integer, ForeignKey("learners.id"))
    module_id = Column(Integer)
    score = Column(Integer)
    total_questions = Column(Integer)
    percentage = Column(Float)
    passed = Column(Boolean)


class LessonProgressDB(Base):
    """Database table for lesson completion."""

    __tablename__ = "lesson_progress"

    id = Column(Integer, primary_key=True, index=True)
    learner_id = Column(Integer, ForeignKey("learners.id"))
    module_id = Column(Integer)
    lesson_id = Column(Integer)
    completed = Column(Boolean, default=False)


Base.metadata.create_all(bind=engine)


# ============================================================
# PYDANTIC MODELS
# ============================================================

class UserAnswer(BaseModel):
    question_id: int
    selected_answer: str


class QuizSubmission(BaseModel):
    learner_id: int
    answers: List[UserAnswer]


class LearnerCreate(BaseModel):
    name: str


# ============================================================
# MODULE DATA
# ============================================================

modules = [
    {
        "id": 1,
        "title": "Internet Basics",
        "description": "Learn the fundamentals of using the internet.",
    },
    {
        "id": 2,
        "title": "Email Basics",
        "description": "Learn how to use email effectively.",
    },
    {
        "id": 3,
        "title": "Online Safety",
        "description": "Learn how to stay safe and protect your information online.",
    },
]


# ============================================================
# LESSON DATA
# ============================================================

lessons = {
    1: [
        {
            "id": 101,
            "title": "What is the Web?",
            "content": "The internet is a global network of computers.",
        },
        {
            "id": 102,
            "title": "Using a Browser",
            "content": "Learn how to use Chrome, Firefox, or Safari.",
        },
    ],
    2: [
        {
            "id": 201,
            "title": "Setting up Email",
            "content": "How to create your first Gmail or Outlook account.",
        },
        {
            "id": 202,
            "title": "Email Etiquette",
            "content": "Professional ways to write and reply to emails.",
        },
    ],
    3: [
        {
            "id": 301,
            "title": "Creating Strong Passwords",
            "content": "Use symbols, numbers, and capital letters.",
        },
        {
            "id": 302,
            "title": "Spotting Phishing",
            "content": "Don't click on suspicious links in emails.",
        },
    ],
}


# ============================================================
# QUIZ DATA
# ============================================================

quizzes_data = {
    1: [
        {
            "id": 1,
            "question": "What is the internet?",
            "options": [
                "A type of computer",
                "A global network of computers",
                "A web browser",
                "An email service",
            ],
            "correct": "A global network of computers",
        },
        {
            "id": 2,
            "question": "Which of these is a web browser?",
            "options": [
                "Google Chrome",
                "Microsoft Word",
                "Windows",
                "Instagram",
            ],
            "correct": "Google Chrome",
        },
        {
            "id": 3,
            "question": "What do you use to find information on the web?",
            "options": [
                "A calculator",
                "A search engine",
                "A printer",
                "A keyboard",
            ],
            "correct": "A search engine",
        },
    ],
    2: [
        {
            "id": 4,
            "question": "What does email stand for?",
            "options": [
                "Electric mail",
                "Electronic mail",
                "Easy mail",
                "Every mail",
            ],
            "correct": "Electronic mail",
        },
        {
            "id": 5,
            "question": "Which symbol is in every email address?",
            "options": [
                "#",
                "$",
                "@",
                "&",
            ],
            "correct": "@",
        },
        {
            "id": 6,
            "question": "What button do you click to write a new email?",
            "options": [
                "Reply",
                "Compose",
                "Forward",
                "Delete",
            ],
            "correct": "Compose",
        },
    ],
    3: [
        {
            "id": 7,
            "question": "What makes a password strong?",
            "options": [
                "Using your name",
                "Using 8+ mixed characters",
                "Using \"password\"",
                "Using only numbers",
            ],
            "correct": "Using 8+ mixed characters",
        },
        {
            "id": 8,
            "question": "What should you do with suspicious links?",
            "options": [
                "Click them immediately",
                "Share with friends",
                "Avoid clicking them",
                "Forward them",
            ],
            "correct": "Avoid clicking them",
        },
        {
            "id": 9,
            "question": "Why should you log out on shared devices?",
            "options": [
                "To save battery",
                "To protect your information",
                "To make it faster",
                "It is not necessary",
            ],
            "correct": "To protect your information",
        },
    ],
}


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():
    return {"message": "Nova Digital Literacy Hub API is running"}


# ============================================================
# MODULES
# ============================================================

@app.get("/modules")
def get_modules():
    return modules


# ============================================================
# LESSONS
# ============================================================

@app.get("/modules/{module_id}/lessons")
def get_lessons(module_id: int):

    if module_id not in lessons:
        raise HTTPException(
            status_code=404,
            detail="Module not found",
        )

    return lessons[module_id]


# ============================================================
# GET QUIZ
# ============================================================

@app.get("/modules/{module_id}/quiz")
def get_quiz(module_id: int):

    if module_id not in quizzes_data:
        raise HTTPException(
            status_code=404,
            detail="Quiz for this module not found",
        )

    # Do not send correct answers to the frontend.
    return [
        {
            "id": question["id"],
            "question": question["question"],
            "options": question["options"],
        }
        for question in quizzes_data[module_id]
    ]


# ============================================================
# CREATE LEARNER
# ============================================================

@app.post("/learners")
def create_learner(
    learner_data: LearnerCreate,
    db: Session = Depends(get_db),
):
    new_learner = LearnerDB(
        name=learner_data.name,
    )

    db.add(new_learner)
    db.commit()
    db.refresh(new_learner)

    return {
        "learner_id": new_learner.id,
        "name": new_learner.name,
    }


# ============================================================
# SUBMIT QUIZ
# ============================================================

@app.post("/modules/{module_id}/quiz")
def submit_quiz(
    module_id: int,
    submission: QuizSubmission,
    db: Session = Depends(get_db),
):
    if module_id not in quizzes_data:
        raise HTTPException(
            status_code=404,
            detail="Quiz not found",
        )

    learner = db.query(LearnerDB).filter(
        LearnerDB.id == submission.learner_id
    ).first()

    if not learner:
        raise HTTPException(
            status_code=404,
            detail="Learner ID not found",
        )

    master_questions = quizzes_data[module_id]
    total_questions = len(master_questions)
    score = 0

    # Prevent duplicate question submissions.
    answered_question_ids = set()

    for user_answer in submission.answers:

        if user_answer.question_id in answered_question_ids:
            continue

        question = next(
            (
                question
                for question in master_questions
                if question["id"] == user_answer.question_id
            ),
            None,
        )

        if question is None:
            continue

        answered_question_ids.add(user_answer.question_id)

        if (
            question["correct"].strip().lower()
            == user_answer.selected_answer.strip().lower()
        ):
            score += 1

    # Prevent the score from exceeding the number of questions.
    score = min(score, total_questions)

    percentage = round(
        (score / total_questions) * 100,
        2,
    )

    passed = percentage >= 70

    new_result = QuizResultDB(
        learner_id=submission.learner_id,
        module_id=module_id,
        score=score,
        total_questions=total_questions,
        percentage=percentage,
        passed=passed,
    )

    db.add(new_result)
    db.commit()
    db.refresh(new_result)

    return {
        "learner_id": submission.learner_id,
        "module_id": module_id,
        "score": score,
        "total_questions": total_questions,
        "percentage": percentage,
        "passed": passed,
    }


# ============================================================
# COMPLETE LESSON
# ============================================================

@app.post(
    "/learners/{learner_id}/modules/{module_id}/lessons/{lesson_id}/complete"
)
def complete_lesson(
    learner_id: int,
    module_id: int,
    lesson_id: int,
    db: Session = Depends(get_db),
):
    learner = db.query(LearnerDB).filter(
        LearnerDB.id == learner_id
    ).first()

    if not learner:
        raise HTTPException(
            status_code=404,
            detail="Learner not found",
        )

    existing = db.query(LessonProgressDB).filter(
        LessonProgressDB.learner_id == learner_id,
        LessonProgressDB.module_id == module_id,
        LessonProgressDB.lesson_id == lesson_id,
    ).first()

    if existing:
        existing.completed = True
    else:
        new_progress = LessonProgressDB(
            learner_id=learner_id,
            module_id=module_id,
            lesson_id=lesson_id,
            completed=True,
        )

        db.add(new_progress)

    db.commit()

    return {
        "learner_id": learner_id,
        "module_id": module_id,
        "lesson_id": lesson_id,
        "completed": True,
    }


# ============================================================
# LEARNER PROGRESS
# ============================================================

@app.get("/learners/{learner_id}/progress")
def get_learner_progress(
    learner_id: int,
    db: Session = Depends(get_db),
):
    learner = db.query(LearnerDB).filter(
        LearnerDB.id == learner_id
    ).first()

    if not learner:
        raise HTTPException(
            status_code=404,
            detail="Learner not found",
        )

    module_progress_list = []
    completed_count = 0

    for module in modules:

        completed_lessons = db.query(LessonProgressDB).filter(
            LessonProgressDB.learner_id == learner_id,
            LessonProgressDB.module_id == module["id"],
            LessonProgressDB.completed == True,
        ).count()

        latest_quiz = db.query(QuizResultDB).filter(
            QuizResultDB.learner_id == learner_id,
            QuizResultDB.module_id == module["id"],
        ).order_by(
            QuizResultDB.id.desc()
        ).first()

        # A module is complete when its quiz is passed.
        is_completed = (
            latest_quiz is not None
            and latest_quiz.passed is True
        )

        if is_completed:
            completed_count += 1

        module_progress_list.append({
            "module_id": module["id"],
            "module_title": module["title"],
            "completed": is_completed,
            "completed_lessons": completed_lessons,
            "latest_quiz_percentage": (
                latest_quiz.percentage
                if latest_quiz
                else None
            ),
        })

    total_modules = len(modules)

    overall_progress = (
        completed_count / total_modules
    ) * 100

    return {
        "learner_id": learner_id,
        "learner_name": learner.name,
        "completed_modules": completed_count,
        "total_modules": total_modules,
        "overall_progress": round(overall_progress, 2),
        "modules": module_progress_list,
    }