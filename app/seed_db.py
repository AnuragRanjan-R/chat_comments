import json
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from pathlib import Path

# This ensures the script can find the 'app' module
# when run from the command line.
# It adds the parent directory (backend) to the Python path.
current_dir = Path(__file__).parent
backend_root = current_dir.parent
sys.path.append(str(backend_root))

from app.database import settings
from app.models import User, Comment, Base
from app.auth import get_password_hash

def seed_database():
    """
    Script to populate the database with data from JSON files.
    It locates data files relative to the script's parent directory.
    """
    print("Starting database seeding process...")

    # --- 1. Setup Database Connection ---
    engine = create_engine(settings.database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    # Drop existing tables and recreate them to ensure a fresh start
    print("Dropping and recreating database tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    # --- 2. Load JSON Data ---
    try:
        # Use backend_root to build the correct path to the JSON files
        with open(backend_root / 'users.json', 'r') as f:
            users_data = json.load(f)
        with open(backend_root / 'comments.json', 'r') as f:
            comments_data = json.load(f)
        print("Successfully loaded JSON data files.")
    except FileNotFoundError as e:
        print(f"Error: {e}. Make sure users.json and comments.json are in the '{backend_root.name}' root directory.")
        return

    # --- 3. Process and Insert Users ---
    print("Seeding users...")
    user_id_map = {}  # Maps old string ID to new integer ID
    default_password = "password123"
    hashed_default_password = get_password_hash(default_password)

    for user_json in users_data:
        # --- FIX: Make the dummy email guaranteed unique ---
        # We append a short, unique part of the user's original ID.
        unique_part = user_json['id'].split('-')[0]
        dummy_email = f"{user_json['name'].replace(' ', '').lower()}+{unique_part}@example.com"
        
        new_user = User(
            name=user_json['name'],
            email=dummy_email,
            hashed_password=hashed_default_password,
            avatar=user_json['avatar'],
            created_at=datetime.fromisoformat(user_json['created_at'].replace('Z', '+00:00'))
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        user_id_map[user_json['id']] = new_user.id
        print(f"  - Created user: {new_user.name} (ID: {new_user.id})")

    # --- 4. Process and Insert Comments ---
    print("Seeding comments...")
    comment_id_map = {} # Maps old comment ID to new integer ID
    comments_data.sort(key=lambda c: c['id'])

    for comment_json in comments_data:
        user_fk = user_id_map.get(comment_json['user_id'])
        parent_fk = comment_id_map.get(comment_json['parent_id']) if comment_json['parent_id'] else None

        if user_fk is not None:
            new_comment = Comment(
                text=comment_json['text'],
                upvotes=comment_json['upvotes'],
                created_at=datetime.fromisoformat(comment_json['created_at'].replace('Z', '+00:00')),
                user_id=user_fk,
                parent_id=parent_fk
            )
            db.add(new_comment)
            db.commit()
            db.refresh(new_comment)
            
            comment_id_map[comment_json['id']] = new_comment.id
            print(f"  - Created comment ID: {new_comment.id} (Parent: {parent_fk})")
        else:
            print(f"  - SKIPPING comment because user_id '{comment_json['user_id']}' was not found.")

    db.close()
    print("\nDatabase seeding complete!")
    print(f"IMPORTANT: A default password '{default_password}' was used for all users.")
    
if __name__ == "__main__":
    seed_database()

