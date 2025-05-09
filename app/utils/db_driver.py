import sqlite3
from fastapi import HTTPException
from typing import Optional
from app.utils.model import User
import os

def _with_cur(func):
    def wrapper(*args, **kwargs):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        db_path = os.path.join(base_dir, "data.db")

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
    # create user table
    user_table = """
    CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    pw TEXT NOT NULL)
    """

    cur.execute(user_table)

    

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




if __name__ == "__main__":
    _init_db()


