from typing import Annotated, List, Optional 
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel,  Relationship, create_engine, select
from datetime import datetime

class User(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str 
    username: str = Field(unique=True)
    password: str
    date_birth: Optional[str] = None
    # Propriedade: List[Nome Tabela] = ?
    annotations: List["Annotation"] = Relationship(back_populates="user")

class Cookies(BaseModel):
    session_user: str
    session_password: str

class Annotation(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    username: str 
    text: str
    book: str
    public: bool 
    date: datetime = Field(default_factory=lambda: datetime.now())
    user_id: int = Field(foreign_key="user.id")
    user: Optional["User"] = Relationship(back_populates="annotations")

# class Book(BaseModel):
#     title: str
#     author: str
#     isbn_10: str


# class Follower(SQLModel, table=True):
#     user_id: int | None = Field(default=None, foreign_key="user.id", primary_key=True)
#     follower_id: int | None = Field(default=None, foreign_key="follower.id", primary_key=True)

# class Following(SQLModel, table=True):
#     user_id: int | None = Field(default=None, foreign_key="user.id", primary_key=True)
#     following_id: int | None = Field(default=None, foreign_key="following.id", primary_key=True)