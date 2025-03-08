from pydantic import BaseModel, EmailStr,field_serializer,Field
from datetime import datetime
from typing import Optional, List,Tuple
from fastapi import UploadFile

class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    pan_number: str
    dob: Optional[datetime] = None
    nationality: Optional[str] = None
    profile_image: Optional[str] = None

class UserSignup(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone_number:str
    gender:str
    password: str = Field(..., min_length=8)
    


    
class UserLogin(BaseModel):
    username:str
    password: str

class UserResponse(BaseModel):
    id: str  # UUID stored as CHAR(36)
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: EmailStr
    phone_number: Optional[str] = None
    pan_number: Optional[str] = None
    dob: Optional[datetime] = None
    nationality: Optional[str] = None
    token: Optional[str] = None  
    profile_image: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    pincode: Optional[int] = None
    employment_status: Optional[str] = None
    avg_investment: Optional[int] = None
    secondary_language: Optional[str] = None
    earning: Optional[int] = None
    profile_question_response: Optional[str] = None
    apartment:Optional[str] = None
    profile_complete: Optional[bool] = None
    created_at: datetime
    updated_at: datetime
    
    @field_serializer("created_at", "updated_at", "dob", mode="plain")
    def serialize_datetime(value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value else None
    class Config:
        from_attributes = True 

class SecurityQuestionCreate(BaseModel):
    question: str

# Response Schema for returning security questions
class SecurityQuestionResponse(BaseModel):
    id: str
    question: str
    created_at:datetime
    
    @field_serializer("created_at")
    def serialize_datetime(value: Optional[datetime]) -> Optional[str]:
        return value.isoformat() if value else None
    class Config:
        from_attributes = True  # Allows ORM conversion

# Request Schema for submitting security question answers
class UserSecurityQuestionAnswer(BaseModel):
    question_id: str
    answer: str  # Will be encrypted before saving

# Request Schema for bulk submission of answers
class UserSecurityQuestionsSubmit(BaseModel):
    email: EmailStr
    answers: List[UserSecurityQuestionAnswer]


class ChangePasswordRequest(BaseModel):
    old_password: str 
    new_password: str 
    confirm_password: str 
    

class ResetPasswordRequest(BaseModel):
    email: str
    new_password: str
    

class RiskAssessmentSchema(BaseModel):
    conversation_history: List[Tuple[str, str]]
    sec_lang: List[Tuple[str, str]]
    class Config:
        from_attributes = True


class RiskAssessmentCreateSchema(BaseModel):
    user_id: int
    conversation_history: List[Tuple[str, str]]
    sec_lang: List[Tuple[str, str]]
    
class RiskAssessmentManageSchema(BaseModel):
    user_id: str
    response: Optional[str] = None
    class Config:
        from_attributes = True
        
