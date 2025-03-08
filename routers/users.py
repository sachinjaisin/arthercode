from fastapi import APIRouter, Depends, HTTPException,Form,File
from sqlalchemy.orm import Session
from models import User,user_security_questions
from schemas import *
from database import SessionLocal
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm,OAuth2PasswordBearer
from auth import *
from pydantic import BaseModel
from datetime import datetime,date
import uuid,os
from sqlalchemy.dialects.postgresql import insert
from email_service import send_email
router = APIRouter()



UPLOAD_FOLDER = "uploaded_images/profile_pics"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
 
def format_response(status: str, message: str, results=None, status_code: int = 200, status_message: str = "OK"):
    if isinstance(results, list):
        results = [result.dict() if isinstance(result, BaseModel) else result for result in results]
    elif isinstance(results, BaseModel):
        results = results.dict()  # If a single result is a Pydantic model
    return JSONResponse(status_code=status_code, content={
        "status": status, 
        "status_code": status_code, 
        "status_message": status_message, 
        "message": message, 
        "results": results or []
    })

def check_profile_completion(user: User, db: Session):
    required_fields = [
        user.first_name, user.last_name, user.address, user.country, user.pincode,
        user.employment_status, user.avg_investment, user.secondary_language
    ]
    
    if all(required_fields):
        user.profile_complete = True
        db.commit()
        db.refresh(user)
        
def is_pan_unique(pan_number: str, db: Session) -> bool:
    """Check if PAN number is unique in the database."""
    return db.query(User).filter(User.pan_number == pan_number).first() is None

@router.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_token(user.id)
    user.token = token
    db.commit()
    db.refresh(user)
    return {"access_token": token, "token_type": "bearer"}

@router.post("/register", response_model=UserResponse)
async def register(user: UserSignup, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        return format_response(
                status="error",
                message="Email is already registered please SignIN",
                status_code=400,
                status_message="Bad Request"
            )
     
    hashed_password = hash_password(user.password)
    user_id = str(uuid.uuid4())  # Generate UUID for user
    token = create_token(user_id)
    
    new_user = User(
        id=user_id,
        email=user.email,
        last_name=user.last_name,
        first_name=user.first_name,
        password_hash=hashed_password,
        gender=user.gender,
        phone_number=user.phone_number,
        token=token,
    )
        
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    otp = generate_otp()
    new_user.otp = otp
    db.commit()
    db.refresh(new_user)
    email_sent = await send_email(user.email, "Welcome to Artha", f"Your verification OTP is: {otp} \n please verify to login into your account")
    if not email_sent:
        return format_response(
            status="error",
            message="Failed to send email",
            status_code=500
        )

    return format_response(
        status="success",
        message="User registered successfully",
        results=UserResponse.from_orm(new_user)
    )
@router.post("/login",)
def login(user: UserLogin, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(
        (User.email == user.username) |
        (User.phone_number == user.username) |
        (User.pan_number == user.username)
    ).first()
    
    if not existing_user:
        return format_response(
                status="error",
                message="User is not register please Signup",
                status_code=400,
                status_message="Bad Request"
            )
    
    if not verify_password(user.password, existing_user.password_hash):
        return format_response(
                status="error",
                message="Invalid Credentials",
                status_code=401,
                status_message="Bad Request"
            )
        
      # Check if email is verified
    if existing_user.email_verified is False:
        return format_response(
            status="error",
            message="Email is not verified. Please verify your email to continue.",
            status_code=403,
            status_message="Forbidden"
        )
    
    # # Check if phone number is verified
    # if not existing_user.is_phone_verified:
    #     return format_response(
    #         status="error",
    #         message="Phone number is not verified. Please verify your phone number to continue.",
    #         status_code=403,
    #         status_message="Forbidden"
    #     )

    # Check if user has accepted Privacy Policy and Terms
    if existing_user.privacy_policy is False or existing_user.terms_condition is False:
        return format_response(
            status="error",
            message="Please accept the Privacy Policy and Terms & Conditions to proceed.",
            status_code=403,
            status_message="Forbidden"
        )
    token = create_token(existing_user.id)
    existing_user.token = token  # Update token field in the database
    
    db.commit()
    db.refresh(existing_user)
    return format_response(
        status="success",
        message="User login successfully",
        results=UserResponse.from_orm(existing_user)
    )


@router.get("/users")
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    
    return format_response(
        status="success",
        message="Users retrieved successfully",
        results=[UserResponse(**user.__dict__) for user in users],
        status_code=200,
    )
@router.get("/users/{user_id}")
def get_user_by_id(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        return format_response(
            status="error",
            message="User not found",
            status_code=404
        )

    return format_response(
        status="success",
        message="User retrieved successfully",
        results=UserResponse(**user.__dict__),
        status_code=200
    )

@router.patch("/update/{user_id}")
def update_user(
    user_id: str,
    first_name: Optional[str] = Form(None),
    last_name: Optional[str] = Form(None),
    phone_number: Optional[str] = Form(None),
    pan_number: Optional[str] = Form(None),
    dob: Optional[str] = Form(None),  # Accept dob as a string
    nationality: Optional[str] = Form(None),
    profile_image: Optional[UploadFile] = File(None),
    address: Optional[str] = Form(None),
    country: Optional[str] = Form(None),
    pincode: Optional[int] = Form(None),
    employment_status: Optional[str] = Form(None),
    profile_question_response: Optional[str] = Form(None),
    gender: Optional[str] = Form(None),
    terms_condition: Optional[bool] = Form(False),
    privacy_policy: Optional[bool] = Form(False),
    earning: Optional[int] = Form(None),
    avg_investment: Optional[int] = Form(None),
    secondary_language: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    # Fetch user by ID
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return format_response(
            status="error",
            message="User not found",
            status_code=404,
            status_message="Not Found"
        )

    # Validate Date of Birth
    dob_date = None
    if dob:
        try:
            dob_date = datetime.strptime(dob, "%Y-%m-%d").date()
            if dob_date >= date.today():
                return format_response(
                    status="error",
                    message="Date of birth cannot be today or in the future",
                    status_code=400,
                    status_message="Bad Request"
                )
        except ValueError:
            return format_response(
                status="error",
                message="Invalid date format. Use YYYY-MM-DD",
                status_code=400,
                status_message="Bad Request"
            )

    # Validate PAN number uniqueness
    if pan_number and not is_pan_unique(pan_number,db):
        return format_response(
            status="error",
            message="PAN number is already linked with another user",
            status_code=400,
            status_message="Bad Request"
        )

    # Handle profile image upload
    if profile_image:
        sanitized_filename = sanitize_filename(profile_image.filename)
        unique_filename = f"{uuid.uuid4()}_{sanitized_filename}"
        file_location = os.path.normpath(os.path.join(UPLOAD_FOLDER, unique_filename))
        with open(file_location, "wb") as buffer:
            buffer.write(profile_image.file.read())
        user.profile_image = file_location

    # Update user fields dynamically
    update_data = {
        "first_name": first_name,
        "last_name": last_name,
        "phone_number": phone_number,
        "pan_number": pan_number,
        "dob": dob_date,
        "nationality": nationality,
        "address": address,
        "country": country,
        "pincode": pincode,
        "employment_status": employment_status,
        "profile_question_response": profile_question_response,
        "gender": gender,
        "terms_condition": terms_condition,
        "privacy_policy": privacy_policy,
        "earning": earning,
        "avg_investment": avg_investment,
        "secondary_language": secondary_language,
    }
    
    for field, value in update_data.items():
        if value is not None:
            setattr(user, field, value)

    user.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(user)

    # Check profile completion status
    check_profile_completion(user, db)

    return format_response(
        status="success",
        message="User profile updated successfully",
        results=UserResponse.from_orm(user)
    )

@router.delete("/users/{user_id}")
def delete_user(user_id: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        return format_response(
            status="error",
            message="User not found",
            status_code=404
        )

    db.delete(user)
    db.commit()

    return format_response(
        status="success",
        message="User deleted successfully",
        status_code=200
    )
    
@router.post("/submit_answers")
def submit_security_answers(
    answers_data: UserSecurityQuestionsSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Ensure user is authenticated
):
    for answer_data in answers_data.answers:
        # Encrypt the answer before saving
        encrypted_answer = encrypt_answer(answer_data.answer)
        stmt = insert(user_security_questions).values(
            user_id=current_user.id,
            question_id=answer_data.question_id,
            answer=encrypted_answer
        ).on_conflict_do_update(
            index_elements=["user_id", "question_id"],
            set_={"answer": encrypted_answer}
        )
        
        db.execute(stmt)
    
    db.commit()
    return format_response(
        status="success",
        message="Security answers saved successfully"
    )


@router.post("/change_password")
def change_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Ensure user is authenticated
):
    user = db.query(User).filter(User.id == current_user.id).first()

    if not user:
        return format_response(
            status="error",
            message="User not found",
            status_code=404,
            status_message="Not Found"
        )
    if not pwd_context.verify(request.old_password, user.password_hash):
        return format_response(
            status="error",
            message="Old password is incorrect",
            status_code=400,
        )
    if request.new_password != request.confirm_password:
        return format_response(
            status="error",
            message="New password and confirm password do not match",
            status_code=400,
        )
    hashed_new_password = hash_password(request.new_password)
    user.password_hash = hashed_new_password
    db.commit()

    return format_response(
        status="success",
        message="Password changed successfully"
    )

@router.post("/verify_otp")
def verify_otp(otp: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user.otp or current_user.otp != otp:
        return format_response(
            status="error",
            message="Invalid OTP",
            status_code=404
        )

    current_user.otp_verified = True
    current_user.otp = None  
    current_user = db.merge(current_user) 
    db.commit()  # Commit the changes
    db.refresh(current_user) 

    return format_response(
        status="success",
        message="OTP verified successfully"
    )

@router.post("/resend_otp")
async def resend_otp(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    otp = generate_otp()
    current_user.otp = otp
    current_user = db.merge(current_user) 
    db.commit()  # Commit the changes
    db.refresh(current_user) 

    email_sent = await send_email(current_user.email, "Your New OTP Code", f"Your new OTP is: {otp}")
    if not email_sent:
        return format_response(
            status="error",
            message="Failed to resend OTP email",
            status_code=500
        )
        
    return format_response(
        status="success",
        message="New OTP sent successfully"
    )
    

@router.post("/forgot_password")
async def forgot_password(username: str, db: Session = Depends(get_db)):
    # Check if user exists
    user = db.query(User).filter(
        (User.email == username) |
        (User.phone_number == username) |
        (User.pan_number == username)
    ).first()
    if not user:
        return format_response(
            status="error",
            message="User not found",
            status_code=404,
            status_message="Not Found"
        )
    otp = generate_otp()

    # Store OTP in the database or in-memory cache (for example, in the user model)
    user.otp = otp
    user.otp_verified = False
    db.commit()
    subject = "Your OTP for password reset"
    body = f"Your OTP for resetting your password is: {otp}"
    # Send reset email
    email_sent = await send_email(user.email,subject,body)
    if not email_sent:
        return format_response(
            status="error",
            message="Failed to resend OTP email",
            status_code=500
        )
    return format_response(
            status="success",
            message="Password reset email sent",
        )

@router.post("/reset_password")
def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()

    if not user:
        return format_response(
            status="error",
            message="User not found",
            status_code=404,
            status_message="Not Found"
        )

    if user.otp_verified==False:
        return format_response(
            status="error",
            message="Otp not verified",
            status_code=404,
            status_message="Not Found"
        )
    # Hash the new password and update it
    hashed_new_password = hash_password(request.new_password)
    user.password_hash = hashed_new_password
    user.otp = None  # Clear the OTP after password reset
    db.commit()

    return format_response(
        status="success",
        message="Password reset successfully"
    )
    
@router.post("profile/verify_otp")
def verify_otp(
    user_id: str,
    otp: str,
    otp_type: str , 
    db: Session = Depends(get_db)
):
    if not otp:
        return format_response(
            status="error",
            message="OTP is required",
            status_code=400
        )

    # Fetch user by ID
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        return format_response(
            status="error",
            message="User not found",
            status_code=404
        )

    # Check the relevant OTP field based on otp_type
    if otp_type == "email":
        if not user.otp or user.otp != otp:
            return format_response(
                status="error",
                message="Invalid OTP for email verification",
                status_code=400
            )
        user.otp = None 
        user.email_verified = True  # Mark email as verified

    elif otp_type == "phone":
        if not user.otp or user.phoneotp != otp:
            return format_response(
                status="error",
                message="Invalid OTP for phone verification",
                status_code=400
            )
        user.phoneotp = None 
        user.phoneno_verified = True  # Mark phone number as verified

    else:
        return format_response(
            status="error",
            message="Invalid OTP type. Use 'email' or 'phone'.",
            status_code=400
        )

    db.commit()
    db.refresh(user)

    return format_response(
        status="success",
        message="OTP verified successfully"
    )
