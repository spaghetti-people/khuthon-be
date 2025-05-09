from pydantic import BaseModel


# 사용자 로그인, 조회용 모델
class User(BaseModel):
    id: str
    pw: str

# 사용자 키울 식물 요청.
class PostUserCrop(BaseModel):
    c_id: int
    name: str

class NewChat(BaseModel):
    c_id: int
    chat: str

class WaterCrop(BaseModel):
    c_id: int
    water: int