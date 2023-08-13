from typing import List
from fastapi import FastAPI, Request
from databases import Database
from decouple import config
from models import post, user
from models import PostStatus, UserRole
from pydantic import BaseModel, validator

DB_USER = str(config("DB_USER"))
DB_PASSWORD = str(config("DB_PASSWORD"))

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@localhost:54321/makepost_db"

db_conn = Database(
    DATABASE_URL
)  # make databse connection using databases library for async


class PostBase(BaseModel):
    title: str
    description: str
    body: str
    status: PostStatus
    user_id: int

class UserBase(BaseModel):
     first_name: str
     last_name: str
     user_name: str
     email_address: str
     role: UserRole

app = FastAPI()


@app.on_event("startup")
async def startup():
    await db_conn.connect()  # establish connection pool


@app.on_event("shutdown")
async def shutdown():
    await db_conn.disconnect()  # disconnect on server shutdown


@app.get("/")
async def root():
    return {"Home": str(post)}


@app.get("/posts/", response_model=List[PostBase])
async def get_all_posts():
    query = post.select()  # using sqlalchemy to generate query string
    resp = await db_conn.fetch_all(
        query=query
    )  # pass query to databases for execution with db
    return resp


@app.post("/create_post/")
async def create_post(new_post: PostBase):
    values = new_post.model_dump()
    query = post.insert()
    resp = await db_conn.execute(query=query, values=values)
    return {"response": resp}


@app.post("/create_user/")
async def create_user(new_user: UserBase):
    values = new_user.model_dump()
    query = user.insert()
    resp = await db_conn.execute(query=query, values=values)
    return {"response": resp}
