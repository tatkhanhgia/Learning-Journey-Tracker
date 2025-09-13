from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import hashlib

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = "learntrack_secret_key_2024"  # In production, use environment variable
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Create the main app without a prefix
app = FastAPI(title="LearnTrack API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_info: dict

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    full_name: str

class Progress(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    level: str
    completed: bool = False
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Note(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    level: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

class ProgressUpdate(BaseModel):
    level: str
    completed: bool

class NoteCreate(BaseModel):
    level: str
    content: str

class NoteUpdate(BaseModel):
    content: str

# Helper functions
def load_users():
    """Load users from users.txt file"""
    users = {}
    try:
        with open(ROOT_DIR / 'users.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    parts = line.split(',')
                    if len(parts) >= 3:
                        username, password, full_name = parts[0], parts[1], parts[2]
                        users[username] = {
                            'password': password,
                            'full_name': full_name
                        }
    except FileNotFoundError:
        logger.error("users.txt file not found")
    return users

def load_levels():
    """Load levels from levels.txt file"""
    levels = []
    try:
        with open(ROOT_DIR / 'levels.txt', 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    levels.append(line)
    except FileNotFoundError:
        logger.error("levels.txt file not found")
    return levels

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
        return username
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )

def prepare_for_mongo(data):
    """Prepare data for MongoDB storage"""
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if isinstance(value, datetime):
                result[key] = value.isoformat()
            else:
                result[key] = value
        return result
    return data

def parse_from_mongo(item):
    """Parse data from MongoDB"""
    if isinstance(item, dict):
        result = {}
        for key, value in item.items():
            if key.endswith('_at') and isinstance(value, str):
                try:
                    result[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except:
                    result[key] = value
            else:
                result[key] = value
        return result
    return item

# Authentication endpoints
@api_router.post("/auth/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    users = load_users()
    
    if request.username not in users:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không đúng"
        )
    
    if users[request.username]['password'] != request.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tên đăng nhập hoặc mật khẩu không đúng"
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": request.username}, expires_delta=access_token_expires
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_info={
            "username": request.username,
            "full_name": users[request.username]['full_name']
        }
    )

@api_router.get("/auth/me")
async def get_current_user(current_user: str = Depends(verify_token)):
    users = load_users()
    if current_user not in users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "username": current_user,
        "full_name": users[current_user]['full_name']
    }

# Configuration endpoints
@api_router.get("/config/levels")
async def get_levels():
    levels = load_levels()
    return {"levels": levels}

@api_router.get("/config/users")
async def get_users(current_user: str = Depends(verify_token)):
    users = load_users()
    user_list = [
        {"username": username, "full_name": data['full_name']}
        for username, data in users.items()
    ]
    return {"users": user_list}

# Progress endpoints
@api_router.get("/progress")
async def get_all_progress(current_user: str = Depends(verify_token)):
    progress_docs = await db.progress.find().to_list(1000)
    levels = load_levels()
    users = load_users()
    
    # Create a dictionary for easy lookup
    progress_dict = {}
    for doc in progress_docs:
        key = f"{doc['username']}_{doc['level']}"
        progress_dict[key] = parse_from_mongo(doc)
    
    # Build complete progress matrix
    result = []
    for username, user_data in users.items():
        user_progress = {
            "username": username,
            "full_name": user_data['full_name'],
            "levels": []
        }
        
        for level in levels:
            key = f"{username}_{level}"
            if key in progress_dict:
                progress_data = progress_dict[key]
                user_progress["levels"].append({
                    "level": level,
                    "completed": progress_data.get('completed', False),
                    "completed_at": progress_data.get('completed_at')
                })
            else:
                user_progress["levels"].append({
                    "level": level,
                    "completed": False,
                    "completed_at": None
                })
        
        result.append(user_progress)
    
    return {"progress": result}

@api_router.get("/progress/me")
async def get_my_progress(current_user: str = Depends(verify_token)):
    progress_docs = await db.progress.find({"username": current_user}).to_list(1000)
    levels = load_levels()
    
    progress_dict = {doc['level']: parse_from_mongo(doc) for doc in progress_docs}
    
    result = []
    for level in levels:
        if level in progress_dict:
            progress_data = progress_dict[level]
            result.append({
                "level": level,
                "completed": progress_data.get('completed', False),
                "completed_at": progress_data.get('completed_at')
            })
        else:
            result.append({
                "level": level,
                "completed": False,
                "completed_at": None
            })
    
    return {"progress": result}

@api_router.post("/progress")
async def update_progress(update: ProgressUpdate, current_user: str = Depends(verify_token)):
    levels = load_levels()
    if update.level not in levels:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid level"
        )
    
    # Check if progress record exists
    existing = await db.progress.find_one({"username": current_user, "level": update.level})
    
    now = datetime.now(timezone.utc)
    progress_data = {
        "username": current_user,
        "level": update.level,
        "completed": update.completed,
        "completed_at": now.isoformat() if update.completed else None,
        "created_at": existing['created_at'] if existing else now.isoformat()
    }
    
    if existing:
        await db.progress.update_one(
            {"username": current_user, "level": update.level},
            {"$set": progress_data}
        )
    else:
        progress_data["id"] = str(uuid.uuid4())
        await db.progress.insert_one(progress_data)
    
    return {"message": "Progress updated successfully"}

# Notes endpoints
@api_router.get("/notes")
async def get_notes(current_user: str = Depends(verify_token)):
    notes_docs = await db.notes.find().sort("created_at", -1).to_list(1000)
    users = load_users()
    
    result = []
    for doc in notes_docs:
        note_data = parse_from_mongo(doc)
        user_full_name = users.get(note_data['username'], {}).get('full_name', note_data['username'])
        result.append({
            "id": note_data['id'],
            "username": note_data['username'],
            "user_full_name": user_full_name,
            "level": note_data['level'],
            "content": note_data['content'],
            "created_at": note_data['created_at'],
            "updated_at": note_data.get('updated_at')
        })
    
    return {"notes": result}

@api_router.post("/notes")
async def create_note(note: NoteCreate, current_user: str = Depends(verify_token)):
    levels = load_levels()
    if note.level not in levels:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid level"
        )
    
    note_data = {
        "id": str(uuid.uuid4()),
        "username": current_user,
        "level": note.level,
        "content": note.content,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.notes.insert_one(note_data)
    return {"message": "Note created successfully", "id": note_data["id"]}

@api_router.put("/notes/{note_id}")
async def update_note(note_id: str, update: NoteUpdate, current_user: str = Depends(verify_token)):
    existing = await db.notes.find_one({"id": note_id})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    # Only the author can update their note
    if existing['username'] != current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own notes"
        )
    
    await db.notes.update_one(
        {"id": note_id},
        {"$set": {
            "content": update.content,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"message": "Note updated successfully"}

@api_router.delete("/notes/{note_id}")
async def delete_note(note_id: str, current_user: str = Depends(verify_token)):
    existing = await db.notes.find_one({"id": note_id})
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Note not found"
        )
    
    # Only the author can delete their note
    if existing['username'] != current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own notes"
        )
    
    await db.notes.delete_one({"id": note_id})
    return {"message": "Note deleted successfully"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()