from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import Query

from . import crud, models, schemas, auth, database

# Create database tables if they don't exist
models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

# CORS Middleware Setup
# Adjust allow_origins for your production frontend URL
origins = [
    "http://localhost",
    "https://chat-comments-fnt-to3v.vercel.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Authentication Endpoints ---

@app.post("/token", response_model=schemas.Token)
def login_for_access_token(db: Session = Depends(database.get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = crud.get_user_by_email(db, email=form_data.username)
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/register", response_model=schemas.User, status_code=status.HTTP_201_CREATED)
def register_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return crud.create_user(db=db, user=user)

@app.get("/users/me", response_model=schemas.User)
def read_users_me(current_user: schemas.User = Depends(auth.get_current_user)):
    return current_user

# --- Comment Endpoints ---

@app.get("/comments", response_model=List[schemas.Comment])
def get_nested_comments(
    db: Session = Depends(database.get_db),
    limit: Optional[int] = Query(default=None, ge=1, description="Limit number of top-level comments returned"),
):
    """
    Fetches all comments and structures them into a nested tree.
    """
    all_comments = crud.get_all_comments(db)
    
    # Create a dictionary for quick lookups
    comment_map = {comment.id: comment for comment in all_comments}
    
    nested_comments = []
    
    for comment in all_comments:
        # Ensure every comment has a 'replies' list initialized
        if not hasattr(comment, 'replies'):
             comment.replies = []

        if comment.parent_id:
            parent = comment_map.get(comment.parent_id)
            if parent:
                # Append the comment to its parent's replies list
                parent.replies.append(comment)
        else:
            # This is a top-level comment
            nested_comments.append(comment)
            
    # Order top-level comments by created_at desc for a stable slice
    try:
        nested_comments.sort(key=lambda c: c.created_at or 0, reverse=True)
    except Exception:
        pass

    if limit is not None:
        return nested_comments[:limit]
    return nested_comments

# --- Logout Endpoint ---
@app.post("/logout")
def logout(current_user: models.User = Depends(auth.get_current_user)):
    # Using stateless JWT; server-side logout is a no-op. Client should discard token.
    return {"detail": "Logged out"}

@app.post("/comments", response_model=schemas.Comment, status_code=status.HTTP_201_CREATED)
def create_new_comment(
    comment: schemas.CommentCreate, 
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    return crud.create_comment(db=db, comment=comment, user_id=current_user.id)

@app.post("/comments/{comment_id}/upvote", response_model=schemas.Comment)
def upvote_a_comment(
    comment_id: int,
    db: Session = Depends(database.get_db),
    # You might want to restrict upvoting to logged-in users
    # current_user: models.User = Depends(auth.get_current_user)
):
    db_comment = crud.upvote_comment(db=db, comment_id=comment_id)
    if not db_comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    return db_comment

@app.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment_endpoint(
    comment_id: int,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    ok = crud.delete_comment(db, comment_id=comment_id, user_id=current_user.id)
    if not ok:
        raise HTTPException(status_code=404, detail="Comment not found or not authorized")
    return
