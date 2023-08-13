from sqlalchemy import func
from sqlalchemy import (
    TEXT,
    Table,
    Column,
    Integer,
    String,
    Text,
    VARCHAR,
    Enum,
    DateTime,
)
from db import metadata_obj
import enum


class UserRole(enum.Enum):
    admin = "admin"
    editor = "editor"


user = Table(
    "user",
    metadata_obj,
    Column("id", Integer, primary_key=True),
    Column("first_name", VARCHAR(64), nullable=False),
    Column("last_name", VARCHAR(64), nullable=False),
    Column("user_name", VARCHAR(128), nullable=False),
    Column("email_address", VARCHAR(128), nullable=False),
    Column("role", Enum(UserRole), nullable=False),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
    Column(
        "last_modified_at",
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    ),
)
