from sqlalchemy import Column, Integer, String, TIMESTAMP,text,Boolean,JSON, ForeignKey, Table,Text,Float,Date,BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base
import uuid
from sqlalchemy.dialects.mysql import CHAR
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

user_security_questions = Table(
    "user_security_questions",
    Base.metadata,
    Column("user_id", String, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("question_id", String, ForeignKey("security_questions.id", ondelete="CASCADE"), primary_key=True),
    Column("answer", String, nullable=False),  # Encrypted answer
    schema="risk"
)

class SecurityQuestion(Base):
    __tablename__ = "security_questions"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    question = Column(String, nullable=False, unique=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))

class User(Base):
    __tablename__ = "users"

    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    email = Column(String, unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)
    phone_number = Column(String,nullable=True)  
    otp = Column(String,nullable=True)  
    phoneotp=Column(String,nullable=True)  
    otp_verified = Column(Boolean,default=False)
    email_verified = Column(Boolean,default=False) 
    phoneno_verified = Column(Boolean,default=False) 
    answer_verified = Column(Boolean,default=False)
    privacy_policy=Column(Boolean,default=False)
    terms_condition=Column(Boolean,default=False)
    pan_number = Column(String, nullable=True)  
    dob = Column(TIMESTAMP(timezone=True), nullable=True)  
    nationality = Column(String, nullable=True)  
    token=Column(Text,nullable=True)
    profile_image = Column(String, nullable=True) 
    gender=Column(String,default='')
    address=Column(Text,default='')
    apartment=Column(Text,default='')
    country=Column(String,default='')
    pincode=Column(Integer,default=0000)
    employment_status=Column(String,default='')
    avg_investment=Column(Integer,default=0000)
    secondary_language=Column(String,default='')
    earning=Column(Integer,default=0000)
    profile_question_response=Column(Text,default='')
    profile_complete=Column(Boolean,default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=text('now()'))
    updated_at = Column(TIMESTAMP(timezone=True), server_default=text('now()')) 

    # Many-to-Many Relationship with Security Questions
    security_questions = relationship("SecurityQuestion", secondary=user_security_questions, backref="users")
    risk_assessments = relationship("RiskAssessment", back_populates="user")

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    conversation_history = Column(MutableList.as_mutable(JSON), default=[])
    sec_lang = Column(MutableList.as_mutable(JSON), default=[])
    assesmentreport=Column(Text,default='')
    user = relationship("User", back_populates="risk_assessments")
    
class StockPrice(Base):
    __tablename__ = "stock_prices"
    
    id = Column(CHAR(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date = Column(Date, nullable=False)
    close = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    open = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)
    ticker = Column(String, nullable=False)