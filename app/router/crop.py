import os

from fastapi import APIRouter, Request
from starlette.responses import JSONResponse
from app.router.auth import login_require, get_session_info
import app.utils.db_driver as db
from datetime import date, timedelta

import requests

from app.utils.model import PostUserCrop

router = APIRouter()


@router.get("/crop", tags=['crop'])
def get_crop():
    data = db.get_crops()

    return JSONResponse(status_code=200, content={'corps': data})

@router.post("/user/crop", tags=['crop'])
@login_require
async def create_user_crop(data: PostUserCrop, request: Request):
    user_info = get_session_info(request)

    db.create_user_crop(data, user_info)

    return JSONResponse(status_code=200, content={'message': '생성 완료.'})

@router.get('/user/crop', tags=['crop'])
@login_require
async def get_user_crops(request: Request, mode: int):
    user_info = get_session_info(request)

    # mode 1 : 컬렉션 화면
    # mode 0 : 메인 화면

    mid = db.get_user_crop(user_info, mode)

    # TODO : db로 요청해서 진행도 획득해야함.
    response = requests.get(os.getenv('REAL_FARM_SERVER') + '/daily_conditions')

    print(response.json())
    res = []

    for m in mid:
        print(m)
        planting_date = date.today() - timedelta(days=m['live_day'])



    return JSONResponse(status_code=200, content={'res': mid})


# @router.get("/crop/create")
# def create_crop:
#     @router.get('/test')
#     @login_require
#     async def test(request: Request):