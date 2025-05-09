from fastapi import APIRouter, Request
from starlette.responses import JSONResponse

from app.router.auth import login_require, get_session_info
from app.utils.model import NewChat

import app.utils.db_driver as db
import requests
import os


router = APIRouter()

@router.post('/chat', tags=['chat'])
@login_require
async def new_chat(request: Request, data: NewChat):

    user_id = get_session_info(request)

    child = {
        'name': '지훈',
        'age': 7,
        "favorite_topics": ["우주", "로봇", "게임"],
        "language_level": "초급",
        "personality": "창의적이고 상상력이 풍부함",
        "learning_style": "놀이를 통한 학습",
    }

    info = db.get_user_crop_info(user_id, data.c_id)

    plant_info = {
        'name': info[0],
        'type': info[1]
    }

    daily_data = requests.get(os.getenv('REAL_FARM_SERVER') + '/daily_conditions').json()

    user_message = data.chat

    payload = {
        'user_id': user_id,
        'plant_info': plant_info,
        'child_profile': child,
        'daily_data': {
            'day': info[2],
            'conditions': daily_data
        },
        'user_message': user_message
    }

    print(payload)

    res = requests.post(os.getenv('AI_SERVER') + "/plant/chat", json=payload)

    return JSONResponse(status_code=200, content={'res': res.json()})

