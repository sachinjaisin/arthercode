from fastapi import APIRouter, Depends, HTTPException,Form,File
from sqlalchemy.orm import Session
from models import User,RiskAssessment
from schemas import *
from database import SessionLocal
from routers.users import format_response
from auth import *
import uuid,os
from sqlalchemy.dialects.postgresql import insert
from sec_lang import generate_and_play_audio,translate_question
from questions import get_next_question
from krutrim_cloud import KrutrimCloud
from datetime import datetime, date
from sqlalchemy.orm.attributes import flag_modified
from assesment import generate_risk_profile


router = APIRouter()
UPLOAD_FOLDER = "uploaded_images/profile_pics"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
def calculate_age(dob):
    today = datetime.today().date()
    # If dob is a string, convert it to a date object.
    if isinstance(dob, str):
        birth_date = datetime.strptime(dob, "%Y-%m-%d").date()
    elif isinstance(dob, datetime):
        birth_date = dob.date()
    elif isinstance(dob, date):
        birth_date = dob
    else:
        return format_response(
                status="error",
                message="Unsupported date format for date of birth.",
                status_code=400,
                status_message="Bad Request"
            )
        
    return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

        
@router.post("/")
async def create_risk_assessment(data: RiskAssessmentManageSchema, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        return format_response(
                status="error",
                message="User is not found please Signup",
                status_code=400,
                status_message="Bad Request"
            )
    if user.profile_complete == False:
        return format_response(
                status="error",
                message="User profile is not complete please update your profile before taking assesment",
                status_code=400,
                status_message="Bad Request"
            ) 
    user_info = {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'address': user.address,
            'country': user.country,
            'pin_code': user.pincode,
            'age': calculate_age(user.dob),
            'employment_status': user.employment_status,
            'avg_investment': user.avg_investment
        }
    # client = KrutrimCloud(api_key='peRaEh89TpUZU_zuAFPMNxFX_QE')
    risk_assessment = db.query(RiskAssessment).filter(RiskAssessment.user_id == data.user_id).first()
    if not risk_assessment:
        risk_assessment = RiskAssessment(
            user_id=data.user_id,
            conversation_history=[],
            sec_lang=[]
        )
        db.add(risk_assessment)
        db.commit()
    if data.response:
        client=KrutrimCloud(api_key='peRaEh89TpUZU_zuAFPMNxFX_QE')
        if risk_assessment.conversation_history==[]:
            initial_question = {
            'type': 'Subjective',
            'question': 'What is your primary financial objective?',
            'hint': 'Please describe your main goal for investments',
            'options': None
            }
            explanation = await translate_question(client,initial_question['question'], initial_question['hint'],language=user.secondary_language)
            audio_response = await generate_and_play_audio(client,explanation,language=user.secondary_language)
            risk_assessment.conversation_history = risk_assessment.conversation_history + [
                    {
                        "question": initial_question["question"],
                        "hint": initial_question["hint"],
                        "response": None,  # Awaiting user input
                    }
                ]
            risk_assessment.sec_lang = risk_assessment.sec_lang + [
                        {
                            "question": initial_question["question"],
                            "explanation": explanation,
                            "audio_response": audio_response,
                        }
                    ]

            db.commit()
            db.refresh(risk_assessment)
            return format_response(
                    status="success",
                    message="Question retrieved successfully",
                    results=[
                        {
                            "initial_question": initial_question,
                            "explanation": explanation,
                            "audio_response": audio_response
                        }
                    ],
                    status_code=200,
                )
        else:
            last_question_idx = len(risk_assessment.conversation_history)
            if last_question_idx > 12:
                return format_response(
                status="error",
                message="Assesment Complete",
                status_code=400,
                status_message="Bad Request"
            ) 
            if not data.response:
                return format_response(
                            status="error",
                            message="Please enter response to continue found",
                            status_code=404,
                            status_message="Not Found"
                        )
                                
            if last_question_idx > 0:
                updated_conversation_history = risk_assessment.conversation_history[:]
                updated_conversation_history[last_question_idx - 1]["response"] = data.response
                risk_assessment.conversation_history = updated_conversation_history
                flag_modified(risk_assessment, "conversation_history")
                db.commit()
                db.refresh(risk_assessment)
            last_question_idx = len(risk_assessment.conversation_history)
            if last_question_idx > 11:
                summary=await generate_risk_profile(client,user_info,risk_assessment.conversation_history)
                risk_assessment.assesmentreport = summary
                db.commit()
                db.refresh(risk_assessment)
                return format_response(
                status="success",
                message="Assesment Complete",
                results=summary,
                status_code=200,
            )
            
            next_question=await get_next_question(client,user_info,risk_assessment.conversation_history)
            explanation = await translate_question(client,next_question['question'], next_question['hint'],language=user.secondary_language)
            audio_response = await generate_and_play_audio(client,explanation,language=user.secondary_language)
            risk_assessment.conversation_history.append({
            "question": next_question['question'],
            "hint": next_question['hint'],
            "response": None  # Awaiting user input
        }) 
            risk_assessment.sec_lang.append({"question": next_question['question'],
            "explantion":explanation,
            "audio_response": audio_response })
            db.commit()
            db.refresh(risk_assessment)
            return format_response(
                    status="success",
                    message="Question retrieved successfully",
                    results=[
                        {
                            "next_question": next_question,
                            "explanation": explanation,
                            "audio_response": audio_response
                        }
                    ],
                    status_code=200,
                )


@router.get("/{user_id}")
def get_risk_assessment(user_id: str, db: Session = Depends(get_db)):
    risk_assessment = db.query(RiskAssessment).filter(RiskAssessment.user_id == user_id).first()

    if not risk_assessment:
        return format_response(
            status="error",
            message="Risk assessment not found for this user",
            status_code=404,
            status_message="Not Found"
        )

    return format_response(
        status="success",
        message="Risk assessment retrieved successfully",
        results={
            "user_id": user_id,
            "conversation_history": risk_assessment.conversation_history,
            "sec_lang": risk_assessment.sec_lang,
            "assesment_summary":risk_assessment.assesmentreport
        }
    )