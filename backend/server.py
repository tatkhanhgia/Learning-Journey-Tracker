from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, UploadFile, File, Form, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import jwt
import re
import aiofiles
import mimetypes
import math

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
app = FastAPI(title="LearnTrack API - Hierarchical")

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

class Session(BaseModel):
    name: str
    type: str  # "session" or "lab"

class Module(BaseModel):
    name: str
    sessions: List[Session]

class Resource(BaseModel):
    name: str
    modules: List[Module]

class LearningStructure(BaseModel):
    resources: List[Resource]

class Progress(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    resource: str
    module: str
    session: str
    completed: bool = False
    completed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Note(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    resource: str
    module: str
    session: str
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

class ProgressUpdate(BaseModel):
    resource: str
    module: str
    session: str
    completed: bool

class NoteCreate(BaseModel):
    resource: str
    module: str
    session: str
    content: str

class NoteUpdate(BaseModel):
    content: str

class Share(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    type: str  # "url" or "file"
    content: str  # URL or file path
    created_by: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    # File specific fields
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None

class ShareCreate(BaseModel):
    title: str
    description: Optional[str] = None
    type: str  # "url" or "file"
    content: str  # URL (for type=url)

class ShareUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    content: Optional[str] = None  # Only for URL updates

class ShareResponse(BaseModel):
    items: List[Share]
    total: int
    page: int
    limit: int
    total_pages: int

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

def parse_learning_structure():
    """Parse the hierarchical learning structure from learning_structure.txt"""
    resources = []
    current_resource = None
    current_module = None
    
    try:
        with open(ROOT_DIR / 'learning_structure.txt', 'r', encoding='utf-8') as f:
            for line in f:
                # Handle both spaces and tabs for indentation
                original_line = line
                line = line.rstrip()
                
                if not line:
                    continue
                
                # Count indentation (convert tabs to 4 spaces for consistency)
                expanded_line = original_line.expandtabs(4)
                indent_level = len(expanded_line) - len(expanded_line.lstrip())
                content = line.strip()
                
                if indent_level == 0:
                    # This is a resource
                    if current_resource:
                        resources.append(current_resource)
                    current_resource = Resource(name=content, modules=[])
                    current_module = None
                    
                elif indent_level <= 4:
                    # This is a module
                    if current_resource:
                        if current_module:
                            current_resource.modules.append(current_module)
                        current_module = Module(name=content, sessions=[])
                        
                elif indent_level <= 8:
                    # This is a session
                    if current_module:
                        session_type = "lab" if content.lower().startswith("lab") else "session"
                        current_module.sessions.append(Session(name=content, type=session_type))
            
            # Don't forget the last resource and module
            if current_module and current_resource:
                current_resource.modules.append(current_module)
            if current_resource:
                resources.append(current_resource)
                
    except FileNotFoundError:
        logger.error("learning_structure.txt file not found")
    
    return LearningStructure(resources=resources)

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

# Structure endpoints
@api_router.get("/structure", response_model=LearningStructure)
async def get_learning_structure():
    """Get the complete learning structure"""
    return parse_learning_structure()

@api_router.get("/structure/resources")
async def get_resources():
    """Get all resources"""
    structure = parse_learning_structure()
    return {"resources": [{"name": resource.name} for resource in structure.resources]}

@api_router.get("/structure/resources/{resource_name}/modules")
async def get_modules(resource_name: str):
    """Get modules for a specific resource"""
    structure = parse_learning_structure()
    
    for resource in structure.resources:
        if resource.name == resource_name:
            return {
                "resource": resource_name,
                "modules": [{"name": module.name} for module in resource.modules]
            }
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Resource not found"
    )

@api_router.get("/structure/resources/{resource_name}/modules/{module_name}/sessions")
async def get_sessions(resource_name: str, module_name: str):
    """Get sessions for a specific module"""
    structure = parse_learning_structure()
    
    for resource in structure.resources:
        if resource.name == resource_name:
            for module in resource.modules:
                if module.name == module_name:
                    return {
                        "resource": resource_name,
                        "module": module_name,
                        "sessions": [{"name": session.name, "type": session.type} for session in module.sessions]
                    }
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Resource or module not found"
    )

# Configuration endpoints
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
    users = load_users()
    structure = parse_learning_structure()
    
    # Create a dictionary for easy lookup
    progress_dict = {}
    for doc in progress_docs:
        key = f"{doc['username']}_{doc['resource']}_{doc['module']}_{doc['session']}"
        progress_dict[key] = parse_from_mongo(doc)
    
    # Build complete progress matrix
    result = []
    for username, user_data in users.items():
        user_progress = {
            "username": username,
            "full_name": user_data['full_name'],
            "resources": []
        }
        
        for resource in structure.resources:
            resource_progress = {
                "name": resource.name,
                "modules": []
            }
            
            for module in resource.modules:
                module_progress = {
                    "name": module.name,
                    "sessions": []
                }
                
                for session in module.sessions:
                    key = f"{username}_{resource.name}_{module.name}_{session.name}"
                    if key in progress_dict:
                        progress_data = progress_dict[key]
                        module_progress["sessions"].append({
                            "name": session.name,
                            "type": session.type,
                            "completed": progress_data.get('completed', False),
                            "completed_at": progress_data.get('completed_at')
                        })
                    else:
                        module_progress["sessions"].append({
                            "name": session.name,
                            "type": session.type,
                            "completed": False,
                            "completed_at": None
                        })
                
                resource_progress["modules"].append(module_progress)
            
            user_progress["resources"].append(resource_progress)
        
        result.append(user_progress)
    
    return {"progress": result}

@api_router.get("/progress/me")
async def get_my_progress(current_user: str = Depends(verify_token)):
    progress_docs = await db.progress.find({"username": current_user}).to_list(1000)
    structure = parse_learning_structure()
    
    progress_dict = {}
    for doc in progress_docs:
        key = f"{doc['resource']}_{doc['module']}_{doc['session']}"
        progress_dict[key] = parse_from_mongo(doc)
    
    result = []
    for resource in structure.resources:
        resource_progress = {
            "name": resource.name,
            "modules": []
        }
        
        for module in resource.modules:
            module_progress = {
                "name": module.name,
                "sessions": []
            }
            
            for session in module.sessions:
                key = f"{resource.name}_{module.name}_{session.name}"
                if key in progress_dict:
                    progress_data = progress_dict[key]
                    module_progress["sessions"].append({
                        "name": session.name,
                        "type": session.type,
                        "completed": progress_data.get('completed', False),
                        "completed_at": progress_data.get('completed_at')
                    })
                else:
                    module_progress["sessions"].append({
                        "name": session.name,
                        "type": session.type,
                        "completed": False,
                        "completed_at": None
                    })
            
            resource_progress["modules"].append(module_progress)
        
        result.append(resource_progress)
    
    return {"progress": result}

@api_router.post("/progress")
async def update_progress(update: ProgressUpdate, current_user: str = Depends(verify_token)):
    # Validate that the resource/module/session exists
    structure = parse_learning_structure()
    found = False
    
    for resource in structure.resources:
        if resource.name == update.resource:
            for module in resource.modules:
                if module.name == update.module:
                    for session in module.sessions:
                        if session.name == update.session:
                            found = True
                            break
    
    if not found:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid resource, module, or session"
        )
    
    # Check if progress record exists
    existing = await db.progress.find_one({
        "username": current_user,
        "resource": update.resource,
        "module": update.module,
        "session": update.session
    })
    
    now = datetime.now(timezone.utc)
    progress_data = {
        "username": current_user,
        "resource": update.resource,
        "module": update.module,
        "session": update.session,
        "completed": update.completed,
        "completed_at": now.isoformat() if update.completed else None,
        "created_at": existing['created_at'] if existing else now.isoformat()
    }
    
    if existing:
        await db.progress.update_one(
            {
                "username": current_user,
                "resource": update.resource,
                "module": update.module,
                "session": update.session
            },
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
            "resource": note_data['resource'],
            "module": note_data['module'],
            "session": note_data['session'],
            "content": note_data['content'],
            "created_at": note_data['created_at'],
            "updated_at": note_data.get('updated_at')
        })
    
    return {"notes": result}

@api_router.post("/notes")
async def create_note(note: NoteCreate, current_user: str = Depends(verify_token)):
    # Validate that the resource/module/session exists
    structure = parse_learning_structure()
    found = False
    
    for resource in structure.resources:
        if resource.name == note.resource:
            for module in resource.modules:
                if module.name == note.module:
                    for session in module.sessions:
                        if session.name == note.session:
                            found = True
                            break
    
    if not found:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid resource, module, or session"
        )
    
    note_data = {
        "id": str(uuid.uuid4()),
        "username": current_user,
        "resource": note.resource,
        "module": note.module,
        "session": note.session,
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

# Create uploads directory
UPLOAD_DIR = ROOT_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# Sharing endpoints
@api_router.get("/shares", response_model=ShareResponse)
async def get_shares(
    page: int = Query(1, ge=1),
    limit: int = Query(10, ge=1, le=50),
    search: str = Query("", description="Search in title and description"),
    type_filter: str = Query("all", description="Filter by type: all, url, file"),
    current_user: str = Depends(verify_token)
):
    """Get paginated shares with search and filter"""
    skip = (page - 1) * limit
    
    # Build filter query
    filter_query = {}
    if search:
        filter_query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]
    
    if type_filter != "all":
        filter_query["type"] = type_filter
    
    # Get total count
    total = await db.shares.count_documents(filter_query)
    
    # Get paginated results
    shares_docs = await db.shares.find(filter_query).sort("created_at", -1).skip(skip).limit(limit).to_list(None)
    
    # Parse shares from MongoDB
    shares = [parse_from_mongo(doc) for doc in shares_docs]
    
    total_pages = math.ceil(total / limit)
    
    return ShareResponse(
        items=shares,
        total=total,
        page=page,
        limit=limit,
        total_pages=total_pages
    )

@api_router.post("/shares")
async def create_share(
    share_data: ShareCreate,
    current_user: str = Depends(verify_token)
):
    """Create a new share item (URL only)"""
    if share_data.type == "file":
        raise HTTPException(status_code=400, detail="Use upload endpoint for files")
    
    if share_data.type == "url" and not share_data.content.startswith(("http://", "https://")):
        raise HTTPException(status_code=400, detail="Invalid URL format")
    
    share = Share(
        title=share_data.title,
        description=share_data.description,
        type=share_data.type,
        content=share_data.content,
        created_by=current_user
    )
    
    await db.shares.insert_one(prepare_for_mongo(share.dict()))
    return {"message": "Share created successfully", "id": share.id}

@api_router.post("/shares/upload")
async def upload_file_share(
    file: UploadFile = File(...),
    title: str = Form(...),
    description: str = Form(""),
    current_user: str = Depends(verify_token)
):
    """Upload and create a file share"""
    # Validate file type
    allowed_types = {
        'image/jpeg', 'image/png', 'image/gif', 'image/webp',
        'application/pdf', 'text/plain', 'text/csv',
        'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'video/mp4', 'video/avi', 'video/mov'
    }
    
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail=f"File type not allowed: {file.content_type}")
    
    # Check file size (10MB limit)
    if file.size > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File size exceeds 10MB limit")
    
    # Generate unique filename
    file_extension = Path(file.filename).suffix
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Save file
    try:
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
    
    # Create share entry
    share = Share(
        title=title,
        description=description,
        type="file",
        content=str(unique_filename),
        created_by=current_user,
        file_name=file.filename,
        file_size=file.size,
        file_type=file.content_type
    )
    
    await db.shares.insert_one(prepare_for_mongo(share.dict()))
    return {"message": "File uploaded successfully", "id": share.id}

@api_router.get("/shares/files/{filename}")
async def get_file(filename: str):
    """Serve uploaded files"""
    file_path = UPLOAD_DIR / filename
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Get mime type
    mime_type, _ = mimetypes.guess_type(str(file_path))
    if not mime_type:
        mime_type = "application/octet-stream"
    
    return FileResponse(file_path, media_type=mime_type)

@api_router.put("/shares/{share_id}")
async def update_share(
    share_id: str,
    share_update: ShareUpdate,
    current_user: str = Depends(verify_token)
):
    """Update a share item"""
    share = await db.shares.find_one({"id": share_id})
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")
    
    if share["created_by"] != current_user:
        raise HTTPException(status_code=403, detail="You can only edit your own shares")
    
    # Prepare update data
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    if share_update.title is not None:
        update_data["title"] = share_update.title
    if share_update.description is not None:
        update_data["description"] = share_update.description
    if share_update.content is not None and share["type"] == "url":
        if not share_update.content.startswith(("http://", "https://")):
            raise HTTPException(status_code=400, detail="Invalid URL format")
        update_data["content"] = share_update.content
    
    await db.shares.update_one({"id": share_id}, {"$set": update_data})
    return {"message": "Share updated successfully"}

@api_router.delete("/shares/{share_id}")
async def delete_share(
    share_id: str,
    current_user: str = Depends(verify_token)
):
    """Delete a share item"""
    share = await db.shares.find_one({"id": share_id})
    if not share:
        raise HTTPException(status_code=404, detail="Share not found")
    
    if share["created_by"] != current_user:
        raise HTTPException(status_code=403, detail="You can only delete your own shares")
    
    # Delete file if it exists
    if share["type"] == "file":
        file_path = UPLOAD_DIR / share["content"]
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception as e:
                logger.warning(f"Failed to delete file {file_path}: {e}")
    
    await db.shares.delete_one({"id": share_id})
    return {"message": "Share deleted successfully"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=False,
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
