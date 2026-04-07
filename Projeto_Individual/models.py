from typing import List, Optional 
from pydantic import BaseModel
from sqlmodel import Field, SQLModel,  Relationship
from datetime import datetime

# Relação User <-- n:n --> User
class Following(SQLModel, table=True):
    user_id: Optional[int]  = Field(default=None, foreign_key="user.id", primary_key=True)
    username: Optional[str]  = Field(default=None, foreign_key="user.username", primary_key=True)

# Relação User <-- 1:n --> Books
# Many to Many relation based on https://github.com/fastapi/sqlmodel/issues/89
class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str 
    username: str = Field(unique=True)
    password: str
    book: List["Book"] = Relationship(back_populates="user")
    following: list["User"] = Relationship(
        back_populates="following",link_model=Following,
        sa_relationship_kwargs=dict(
            secondaryjoin="User.id==Following.user_id",
            primaryjoin="User.username==Following.username",
        )
    )

class Cookies(BaseModel):
    session_user: str = ""
    session_password: str = ""

# Relação Book <-- 1:n --> Anottation
class Annotation(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    username: str 
    text: str
    public: bool 
    date: datetime = Field(default_factory=lambda: datetime.now())
    book_id: int = Field(foreign_key="book.id")
    book: Optional["Book"] = Relationship(back_populates="annotations")

# Relação User <-- 1:n --> Books
# Relação Book <-- 1:n --> Annotation
class Book(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    title: str 
    author: str
    summary: Optional[str]
    public: bool 
    date: datetime = Field(default_factory=lambda: datetime.now())
    user_id: int = Field(foreign_key="user.id")
    user: Optional["User"] = Relationship(back_populates="book")
    annotations: List["Annotation"] = Relationship(back_populates="book")