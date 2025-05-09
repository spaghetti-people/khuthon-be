from pydantic import BaseModel


# 사용자 로그인, 조회용 모델
class User(BaseModel):
    id: str
    pw: str