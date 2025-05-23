import os
from http.client import HTTPResponse

from fastapi import APIRouter, Request, Response
from fastapi.responses import StreamingResponse
from starlette.responses import JSONResponse
from app.router.auth import login_require, get_session_info
import app.utils.db_driver as db
from datetime import date, timedelta
from app.router.predict import SensorData
from pydantic import BaseModel
import pandas as pd
from app.utils.predict import preprocess_data, normalize_prediction
import joblib
from pathlib import Path
from io import BytesIO

import requests

from app.utils.model import PostUserCrop, WaterCrop

router = APIRouter()


model_path = Path(__file__).parent.parent / "utils" / "models" / "crop_growth_model.pkl"
if not model_path.exists():
    raise RuntimeError("모델 파일을 찾을 수 없습니다.")
model = joblib.load(model_path)


@router.get("/crop", tags=["crop"])
def get_crop():
    data = db.get_crops()

    return JSONResponse(status_code=200, content={"corps": data})


@router.post("/user/crop", tags=["crop"])
@login_require
def create_user_crop(data: PostUserCrop, request: Request):
    user_info = get_session_info(request)

    db.create_user_crop(data, user_info)

    return JSONResponse(status_code=200, content={"message": "생성 완료."})


@router.get("/user/crop", tags=["crop"])
@login_require
def get_user_crops(request: Request, mode: int):
    user_info = get_session_info(request)

    # mode 1 : 컬렉션 화면 -> 성장 완료된 데이터.
    # mode 0 : 메인 화면 -> 성장 중 인 데이터.

    mid = db.get_user_crop(user_info, mode)

    # TODO : db로 요청해서 진행도 획득해야함.
    response = requests.get(
        os.getenv("REAL_FARM_SERVER") + "/daily_conditions_progress"
    ).json()

    print(response)
    res = []

    for m in mid:
        print(m)
        planting_date = date.today() - timedelta(days=m["live_day"])

        input_data = pd.DataFrame([response])
        processed_data = preprocess_data(input_data)
        prediction = model.predict(processed_data)[0]
        normalized_prediction = normalize_prediction(prediction)
        if normalized_prediction >= 80:
            evaluation = "매우 좋음"
        elif normalized_prediction >= 60:
            evaluation = "좋음"
        elif normalized_prediction >= 40:
            evaluation = "보통"
        elif normalized_prediction >= 20:
            evaluation = "나쁨"
        else:
            evaluation = "매우 나쁨"

        m["evaluation_rate"] = normalized_prediction
        m["evaluation"] = evaluation

        res.append(m)
    return JSONResponse(status_code=200, content={"res": res})


@router.post("/water", tags=["crop"])
@login_require
def water(request: Request, data: WaterCrop):
    uid = get_session_info(request)

    res = db.water_crops(uid, data.c_id, data.water)

    # 오늘 물을 더 줄 수 있는 경우. 물 주기.
    if res is not None:
        requests.post(
            os.getenv("REAL_FARM_SERVER") + "/water", json={"water": data.water}
        )

    return JSONResponse(status_code=200, content={"res": res})


@router.get("/time/{c_id}", tags=["crop"])
@login_require
def get_time(request: Request, c_id: int):

    uid = get_session_info(request)

    row = db.get_user_time(uid, c_id)

    filename, content = row

    return StreamingResponse(BytesIO(content), media_type="video/mp4")
    # return Response(content, media_type="video/mp4", headers={"Content-Disposition": f"inline; filename={filename}"})


# @router.get("/crop/create")
# def create_crop:
#     @router.get('/test')
#     @login_require
#     async def test(request: Request):
