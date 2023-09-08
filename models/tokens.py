import secrets

from datetime import datetime, timedelta
from sqlalchemy import (
    String,
    Table,
    Column,
    Integer,
    DateTime,
)
from db import metadata_obj


def generate_token() -> str:
    return secrets.token_urlsafe(32)

def generate_expire_datetime() -> datetime:
    return datetime.utcnow() + timedelta(minutes=30)


tokens = Table(
    "tokens",
    metadata_obj,
    Column("id", Integer, primary_key=True),
    Column("user_id", String, nullable=False),
    Column("access_token", String, nullable=False, default=generate_token()),
    Column("expiration_date", DateTime, nullable=False, default=generate_expire_datetime()),
)
