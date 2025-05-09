from fastapi import APIRouter, Request
from starlette.responses import JSONResponse
from app.router.auth import login_require, get_session_info
import app.utils.db_driver as db

router = APIRouter()


@router.get("/crop", tags=['crop'])
def get_crop():
    data = db.get_crops()

    return JSONResponse(status_code=200, content={'corps': data})

@router.post("/crop/{c_id}", tags=['crop'])
@login_require
async def create_user_crop(c_id: int, request: Request):
    user_info = get_session_info(request)

    db.create_user_crop(c_id, user_info)

    return JSONResponse(status_code=200, content={'message': '생성 완료.'})

# @router.get("/crop/create")
# def create_crop:
#     @router.get('/test')
#     @login_require
#     async def test(request: Request):