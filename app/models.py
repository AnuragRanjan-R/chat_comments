from sqlalchemy import Column, Integer, String, Text, ForeignKey, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class User(Base):
    """
    User model for storing user details.
    """
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    avatar = Column(String(255), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    comments = relationship("Comment", back_populates="user")

class Comment(Base):
    """
    Comment model with a self-referencing relationship for nesting.
    """
    __tablename__ = "comments"
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    upvotes = Column(Integer, default=0)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("comments.id"), nullable=True) # Self-reference
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="comments")
    
    # The relationship to fetch replies for a comment
    replies = relationship("Comment", back_populates="parent", cascade="all, delete-orphan")
    
    # The relationship to link a reply to its parent
    parent = relationship("Comment", back_populates="replies", remote_side=[id])
