from datetime import datetime
from typing import Any, List
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.security import (
    APIKeyHeader,
    OAuth2PasswordRequestForm,
    OAuth2PasswordBearer,
)
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from databases import Database
from decouple import config
from models import posts, users, tokens
from models import PostStatus, UserRole, generate_token, generate_expire_datetime
from pydantic import BaseModel
from asyncpg.exceptions import UniqueViolationError

from passlib.context import CryptContext

DB_USER = str(config("DB_USER"))
DB_PASSWORD = str(config("DB_PASSWORD"))
API_TOKEN = str(config("API_TOKEN"))

api_key_header = APIKeyHeader(name="Token")

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
    email_address: str
    user_name: str
    role: UserRole


class UserCreate(UserBase):
    first_name: str
    last_name: str
    password: str


class UserDB(UserBase):
    hashed_password: str


#### AUTHENTICATION ####
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_hashed_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


async def authenticate(email: str, password: str) -> Any:
    query = """
        SELECT email_address, hashed_password FROM users WHERE email_address = :email
    """

    try:
        user = await db_conn.fetch_one(query, values={"email": email})
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User does not exist."
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User does not exist."
        )

    if not verify_password(password, user["hashed_password"]):  # type: ignore
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username or password is incorrect.",
        )

    return user


async def create_access_token(user_id: str) -> Any:
    access_token = generate_token()
    expiration_date = generate_expire_datetime()
    insert_values = {
        "user_id": user_id,
        "access_token": access_token,
        "expiration_date": expiration_date,
    }
    insert_query = tokens.insert()

    token_id = await db_conn.execute(query=insert_query, values=insert_values)

    select_query = tokens.select().where(tokens.c.id == token_id)
    raw_token = await db_conn.fetch_one(query=select_query)  # type: ignore
    access_token = raw_token["access_token"]  # type: ignore

    return {"access_token": access_token, "token_type": "bearer"}


async def get_current_user(
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="/token")),
):
    get_token_query = tokens.select().where(tokens.c.access_token == token)
    raw_token = await db_conn.fetch_one(query=get_token_query)  # type: ignore
    access_user = raw_token["user_id"]  # type: ignore
    expiration_date = raw_token["expiration_date"]  # type: ignore

    if datetime.utcnow() < expiration_date:
        return {"access_token": access_user, "expiration_date": expiration_date}
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has timed out, please login again.",
        )


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
async def startup():
    await db_conn.connect()  # establish connection pool


@app.on_event("shutdown")
async def shutdown():
    await db_conn.disconnect()  # disconnect on server shutdown


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    post_title = "A new landing page"
    return templates.TemplateResponse(
        "index.html", {"request": request, "post_title": post_title}
    )


@app.post("/token")
async def create_token(
    form_data: OAuth2PasswordRequestForm = Depends(OAuth2PasswordRequestForm),
):
    email = form_data.username
    password = form_data.password

    resp = await authenticate(email, password)
    token = await create_access_token(resp["email_address"])
    return token


@app.get("/protected_route")
async def protected_route(user: UserBase = Depends(get_current_user)):
    return user


@app.get("/posts/", response_model=List[PostBase])
async def get_all_posts():
    query = posts.select()  # using sqlalchemy to generate query string
    resp = await db_conn.fetch_all(
        query=query
    )  # pass query to databases for execution with db
    return resp


@app.post("/create_post/")
async def create_post(
        new_post: PostBase, 
        current_user: UserBase=Depends(get_current_user)
):
    if current_user:
        values = new_post.model_dump()
        query = posts.insert()
        resp = await db_conn.execute(query=query, values=values)
        return {"response": resp}


@app.post("/create_user/")
async def create_user(new_user: UserCreate):
    values = new_user.model_dump()
    hashed_password = get_hashed_password(values["password"])
    create_new_user = {
        "email_address": values["email_address"],
        "user_name": values["user_name"],
        "role": values["role"],
        "first_name": values["first_name"],
        "last_name": values["last_name"],
        "hashed_password": hashed_password,
    }
    query = users.insert()
    try:
        resp = await db_conn.execute(query=query, values=create_new_user)
    except UniqueViolationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists."
        )
    return {"response": resp}
