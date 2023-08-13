from sqlalchemy import (
    TEXT,
    DateTime,
    ForeignKey,
    Table,
    Column,
    Integer,
    String,
    Text,
    VARCHAR,
    Enum,
)
from sqlalchemy import func
from db import metadata_obj
import enum


class PostStatus(enum.Enum):
    draft = "draft"
    published = "published"


post = Table(
    "post",
    metadata_obj,
    Column("id", Integer, primary_key=True),
    Column("title", TEXT, nullable=False),
    Column("description", TEXT, nullable=False),
    Column("body", TEXT, nullable=False),
    Column("status", Enum(PostStatus), nullable=False),
    Column("user_id", ForeignKey("user.id")),
    Column("created_at", DateTime, server_default=func.now(), nullable=False),
    Column(
        "last_modified_at",
        DateTime,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    ),
)
