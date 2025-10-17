from sqlalchemy.orm import Session
from . import models, schemas, auth

# --- User CRUD ---
def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()

def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(email=user.email, name=user.name, hashed_password=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# --- Comment CRUD ---
def get_all_comments(db: Session):
    return db.query(models.Comment).all()

def create_comment(db: Session, comment: schemas.CommentCreate, user_id: int):
    db_comment = models.Comment(**comment.model_dump(), user_id=user_id)
    db.add(db_comment)
    db.commit()
    db.refresh(db_comment)
    return db_comment

def upvote_comment(db: Session, comment_id: int):
    db_comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if db_comment:
        db_comment.upvotes += 1
        db.commit()
        db.refresh(db_comment)
    return db_comment

def delete_comment(db: Session, comment_id: int, user_id: int) -> bool:
    comment = db.query(models.Comment).filter(models.Comment.id == comment_id).first()
    if not comment:
        return False
    if comment.user_id != user_id:
        return False
    db.delete(comment)
    db.commit()
    return True