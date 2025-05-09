import sqlite3
from http.cookiejar import reach

from fastapi import HTTPException
from typing import Optional
from app.utils.model import User, PostUserCrop
import os

def _with_cur(func):
    def wrapper(*args, **kwargs):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(base_dir)
        db_path = os.path.join(parent_dir, "data.db")

        conn = sqlite3.connect(db_path)
        try:
            result = func(*args, cur=conn.cursor(), **kwargs)
        finally:
            conn.commit()
            conn.close()

        return result
    return wrapper


@_with_cur
def _init_db(cur: Optional[sqlite3.Cursor] = None):
    cur.execute("PRAGMA foreign_keys = ON")

    # create user table
    cur.execute("DROP TABLE user_water")
    cur.execute("DROP TABLE login_user")
    cur.execute("DROP TABLE video_water")
    cur.execute("DROP TABLE user_crops")
    cur.execute("DROP TABLE users")

    user_table = """
    CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    pw TEXT NOT NULL)
    """

    cur.execute(user_table)

    # 사용자가 키우고 있는 식물 테이블

    crops_table = """
    CREATE TABLE IF NOT EXISTS user_crops (
    nums INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    crop_id INTEGER,
    nick_name TEXT,
    live_day INTEGER DEFAULT 1,
    is_end INTEGER DEFAULT 0,
    FOREIGN KEY (crop_id) REFERENCES crops(crop_id),
    FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """

    cur.execute(crops_table)

    # 로그인된 사용자를 저장하는 테이블

    login_table = """
    CREATE TABLE IF NOT EXISTS login_user (
    login_id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT,
    user_id TEXT
    )
    """

    cur.execute(login_table)

    # 오늘 사용자가 물준양.


    water_table = """
    CREATE TABLE IF NOT EXISTS user_water (
    water_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    crop_id INTEGER,
    now_water INTEGER DEFAULT 0,
    max_water INTEGER DEFAULT 1000,
    FOREIGN KEY (crop_id) REFERENCES user_crops(nums),
    FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """

    cur.execute(water_table)

    # video_table = ""

    video_table = """
    CREATE TABLE IF NOT EXISTS video_water (
    video_id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    crop_id INTEGER,
    video BLOB,
    FOREIGN KEY (crop_id) REFERENCES user_crops(nums),
    FOREIGN KEY (user_id) REFERENCES users(id)
    )
    """

    cur.execute(video_table)

    pass


@_with_cur
def get_user(user: User, cur: Optional[sqlite3.Cursor] = None):

    cur.execute("SELECT id, pw FROM users WHERE id = ?", (user.id,))

    old = cur.fetchone()

    if old is None:
        raise HTTPException(status_code=404, detail='Can not find user')

    return [old[0], old[1]]


@_with_cur
def join(id, pw, cur: Optional[sqlite3.Cursor] = None):
    # 중복 사용자 확인.
    cur.execute("SELECT * FROM users WHERE id = ?", (id,))

    have = cur.fetchone()

    if have is not None:
        raise HTTPException(status_code=400, detail='User duplication')

    # 저장.
    cur.execute("INSERT INTO users(id, pw) VALUES(?, ?)", (id, pw))

    # 성공한 작물 추가.
    query = "INSERT INTO user_crops(user_id, crop_id, nick_name, is_end) VALUES(?, ?, ?, ?)"
    cur.execute(query, (id, 1, '누룽지', 1))

    # 타임 랩스 추가.
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # 현재 파일 위치
    file_path = os.path.join(BASE_DIR, "test.mp4")

    print(file_path)
    with open(file_path, 'rb') as f:
        data = f.read()

        query = "INSERT INTO video_water(user_id, crop_id, video) VALUES (?, ?, ?)"
        cur.execute(query, (id, 1, data))


@_with_cur
def get_crops(cur: Optional[sqlite3.Cursor] = None):
    cur.execute("SELECT crop_id, crop_name_KOR FROM crops")

    result = []

    for d in cur.fetchall():
        result.append({
            'crop_id': d[0],
            'crop_name': d[1]
        })

    return result


@_with_cur
def create_user_crop(data: PostUserCrop, user_id: str, cur: Optional[sqlite3.Cursor] = None):
    query = "INSERT INTO user_crops(user_id, crop_id, nick_name) VALUES (?, ?, ?)"

    try:
        cur.execute(query, (user_id, data.c_id, data.name))
    except Exception as e:
        raise HTTPException(status_code=400, detail='닉네임이 중복되었습니다.')

@_with_cur
def login(key: str, user_id: str, cur: Optional[sqlite3.Cursor] = None):
    cur.execute("SELECT * FROM login_user WHERE user_id = ?", (user_id,))

    res = cur.fetchone()

    if res is not None:
        raise HTTPException(status_code=401, detail="이미 로그인 하였습니다.")

    query = "INSERT INTO login_user(key, user_id) VALUES(?, ?)"

    try:
        cur.execute(query, (key, user_id))
    except Exception as e:
        raise HTTPException(status_code=400, detail='해당 사용자가 존재하지 않습니다.')

@_with_cur
def logout(key: str, cur: Optional[sqlite3.Cursor] = None):
    cur.execute("DELETE FROM login_user WHERE key = ?", (key,))

@_with_cur
def verify_session(key: str, cur: Optional[sqlite3.Cursor] = None):
    cur.execute("SELECT * FROM login_user WHERE key = ?", (key,))

    user = cur.fetchone()

    if user is None:
        return False
    return True

@_with_cur
def get_session_info(key: str, cur: Optional[sqlite3.Cursor] = None):
    cur.execute("SELECT user_id FROM login_user WHERE key = ?", (key, ))

    user = cur.fetchone()

    if user is None:
        return None
    return user[0]

@_with_cur
def get_user_crop(uid: str, mode: int, cur: Optional[sqlite3.Cursor] = None):
    query = "SELECT nums, nick_name, live_day, is_end, crop_id FROM user_crops WHERE user_id = ?"
    cur.execute(query, (uid,))

    res = []

    tmp = cur.fetchall()
    for data in tmp:

        print("d:", data)

        if data[3] != mode:
            continue

        query = "SELECT crop_name_KOR FROM crops WHERE crop_id = ?"
        cur.execute(query, (data[4],))

        name = cur.fetchone()[0]

        res.append({
            'crop_id': data[0],
            'nick_name': data[1],
            'crop_name': name,
            'live_day': data[2],
            'is_end': data[3],
        })

    return res

# 채팅에 필요한 정보.
@_with_cur
def get_user_crop_info(uid: str, c_id: int, cur: Optional[sqlite3.Cursor] = None):
    query = "SELECT nick_name, live_day, crop_id FROM user_crops WHERE user_id = ? and nums = ?"
    cur.execute(query, (uid, c_id))

    data = cur.fetchone()
    print('data: ', data)

    if data is None:
        raise HTTPException(status_code=404, detail='사용자가 해당 식물을 안 키웁니다.')

    query = "SELECT crop_name_KOR FROM crops WHERE crop_id = ? "
    cur.execute(query, (data[2],))

    plant = cur.fetchone()

    print('plant: ', plant)

    if plant is None:
        raise HTTPException(status_code=404, detail='해당 식물이 존재하지 않습니다.')

    return [data[0], plant[0], data[1]]
    pass

@_with_cur
def water_crops(uid: str, c_id: int, water, cur: Optional[sqlite3.Cursor] = None):
    query = "SELECT now_water, max_water FROM user_water WHERE user_id = ? and crop_id = ?"
    cur.execute(query, (uid, c_id))

    data = cur.fetchone()

    if data is None:
        query = "INSERT INTO user_water(user_id, crop_id, now_water) VALUES (?, ?, ?)"
        cur.execute(query, (uid, c_id, water))
        return ""

    if data[0] + water > data[1]:
        return "too many water"

    query = "UPDATE user_water SET now_water = ? WHERE user_id = ? and crop_id = ?"
    cur.execute(query, (data[0] + water, uid, c_id))

    return "ok"

@_with_cur
def get_user_time(uid: str, c_id: int, cur: Optional[sqlite3.Cursor] = None):
    query = "SELECT video FROM video_water WHERE user_id = ? and crop_id = ?"
    cur.execute(query, (uid, c_id))

    data = cur.fetchone()

    if data is None:
        raise HTTPException(status_code=404, detail='video data not found')

    return [uid + str(c_id), data[0]]


if __name__ == "__main__":
    _init_db()


