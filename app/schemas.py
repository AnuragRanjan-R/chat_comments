from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

# --- User Schemas ---
class UserBase(BaseModel):
    name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    avatar: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

# --- Token Schemas ---
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None

# --- Comment Schemas ---
class CommentBase(BaseModel):
    text: str

class CommentCreate(CommentBase):
    parent_id: Optional[int] = None

# This is the main schema for returning a comment, including its nested replies.
class Comment(CommentBase):
    id: int
    upvotes: int
    user: User
    replies: List['Comment'] = []  # The magic for nesting
    created_at: datetime

    class Config:
        from_attributes = True

# This is crucial for Pydantic to handle the recursive 'Comment' schema.
Comment.model_rebuild()
