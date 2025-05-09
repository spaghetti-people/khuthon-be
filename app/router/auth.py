import hashlib
import uuid

from fastapi import APIRouter, Response, Request, HTTPException
from fastapi.responses import JSONResponse
from functools import wraps
import app.utils.db_driver as db
from app.utils.model import User


router = APIRouter()

session_store = {}

# 비밀번호 해시 함수
def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def get_session_id(request: Request):
    return request.headers.get('Authorization')

def login_require(func):
    @wraps(func)
    async def wrapper(request: Request, *args, **kwargs):
        code = get_session_id(request)

        if code not in session_store:
            raise HTTPException(status_code=401, detail='Need login.')

        return await func(request=request, *args, **kwargs)
    return wrapper


@router.post('/login',summary='로그인', tags=['auth'])
def login(request: Request, user: User):
    origin = db.get_user(user)

    now = hash_pw(user.pw)

    if origin[0] == user.id and origin[1] == now:
        session_id = str(uuid.uuid4())

        session_store[session_id] = {'user': user.id}
        return JSONResponse(status_code=200, content={'message': '로그인 성공', 'session': session_id})

    return JSONResponse(status_code=401, content={'message': '로그인 실패'})
    pass


@router.post('/join', summary='회원 가입', tags=['auth'])
def join(user: User):
    db.join(user.id, hash_pw(user.pw))

    return JSONResponse(content={'message': '회원 가입 성공.'}, status_code=200)

@router.get('/logout', summary="로그아웃", tags=['auth'])
@login_require
def logout(request: Request):
    sid = get_session_id(request)

    session_store.pop(sid, None)

    return JSONResponse(status_code=200, content={'message': '로그아웃 성공.'})


@router.get('/test')
@login_require
async def test(request: Request):
    return JSONResponse(content={'message': 'test'}, status_code=200)