from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from models import SecurityQuestion, User, user_security_questions
from database import get_db
from typing import List
import uuid
from auth import *
from schemas import *
from routers.users import format_response
from sqlalchemy.sql import text

router = APIRouter()


@router.get("/", response_model=List[SecurityQuestionResponse])
def get_security_questions(db: Session = Depends(get_db)):
    questions = db.query(SecurityQuestion).all()
    return format_response(
        status="success",
        message="Security questions fetched successfully",
        results=[SecurityQuestionResponse.from_orm(q) for q in questions]
    )

@router.get("/{question_id}", response_model=SecurityQuestionResponse)
def get_security_question_by_id(question_id: str, db: Session = Depends(get_db)):
    question = db.query(SecurityQuestion).filter(SecurityQuestion.id == question_id).first()
    
    if not question:
        return format_response(
            status="error",
            message="Security question not found",
            status_code=404,
            status_message="Not Found"
        )

    return format_response(
        status="success",
        message="Security question retrieved successfully",
        results=SecurityQuestionResponse.from_orm(question)
    )

@router.post("/", response_model=SecurityQuestionResponse)
def create_security_question(question_data: SecurityQuestionCreate, db: Session = Depends(get_db)):
    existing_question = db.query(SecurityQuestion).filter(SecurityQuestion.question == question_data.question).first()
    if existing_question:
        return format_response(
            status="error",
            message="Question already exists",
            status_code=400
        )

    new_question = SecurityQuestion(question=question_data.question)
    db.add(new_question)
    db.commit()
    db.refresh(new_question)
    return format_response(
        status="success",
        message="Security question added successfully",
        results=SecurityQuestionResponse.from_orm(new_question)
    )

@router.post("/verify_answers")
def verify_security_answers(
    verify_data: UserSecurityQuestionsSubmit,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.email == verify_data.email).first()
    if not user:
        return format_response(
            status="error",
            message="User not found",
            status_code=400
        )

    for answer_data in verify_data.answers:
        encrypted_answer = hashlib.sha256(answer_data.answer.encode()).hexdigest()

        query = db.execute(
            text(
                """
                SELECT * FROM risk.user_security_questions
                WHERE user_id = :user_id AND question_id = :question_id AND answer = :encrypted_answer
                """
            ),
            {"user_id": user.id, "question_id": answer_data.question_id, "encrypted_answer": encrypted_answer}
        ).fetchone()

        if query:
            user.answer_verified = True
            db.commit()

            return format_response(
                status="success",
                message="Security answers verified successfully.",
            )
    return format_response(
            status="error",
            message="All answers are incorrect.",
            status_code=400
        )
  
@router.delete("/{question_id}")
def delete_security_question(question_id: str, db: Session = Depends(get_db)):
    question = db.query(SecurityQuestion).filter(SecurityQuestion.id == question_id).first()
    
    if not question:
        return format_response(
            status="error",
            message="Security question not found",
            status_code=404,
            status_message="Not Found"
        )
    
    db.delete(question)
    db.commit()

    return format_response(
        status="success",
        message="Security question deleted successfully"
    )