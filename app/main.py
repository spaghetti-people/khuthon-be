import uvicorn
import os
from dotenv import load_dotenv

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from router.auth import router as auth_router
from utils.db_driver import _init_db


from router.test import router as test_router


# 환경 변수 로딩
load_dotenv()


app = FastAPI()

origins = [
    'http://localhost:3000',
    'http://localhost:8000',
    'http://localhost:8080'
]

# CORS 추가
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=os.getenv("SECRET_KEY"))

# 라우터 추가
app.include_router(auth_router)
app.include_router(test_router)

if __name__ == "__main__":
    _init_db()
    uvicorn.run("main:app", host='127.0.0.1', port=8000, reload=True)

