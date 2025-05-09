import sqlite3
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

    login_table = """
    CREATE TABLE IF NOT EXISTS login_user (
    login_id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT,
    user_id TEXT
    )
    """

    cur.execute(login_table)
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
        raise HTTPException(status_code=400, detail='해당 곡물이 존재하지 않습니다.')

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
    query = "SELECT crop_id, nick_name, live_day, is_end FROM user_crops WHERE user_id = ?"
    cur.execute(query, (uid,))

    res = []

    for data in cur.fetchall():
        if data[3] > mode:
            continue

        res.append({
            'crop_id': data[0],
            'nick_name': data[1],
            'live_day': data[2],
        })

    return res


if __name__ == "__main__":
    _init_db()


