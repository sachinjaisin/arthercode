from fastapi import FastAPI
from database import Base, engine
from fastapi.middleware.cors import CORSMiddleware
from routers import users,security_questions,riskassesment,stocks

Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(security_questions.router,prefix="/security_questions", tags=["Security Questions"])
app.include_router(riskassesment.router,prefix="/riskassesment", tags=["Assesment Questions"])
app.include_router(stocks.router, prefix="/stocks", tags=["stocks"])