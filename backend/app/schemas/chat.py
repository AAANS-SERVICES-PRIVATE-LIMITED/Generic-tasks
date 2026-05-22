from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from app.schemas.message import MessageRead

class ChatBase(BaseModel):
    title: Optional[str] = "New Chat"

class ChatCreate(ChatBase):
    user_id: str

class ChatRead(ChatBase):
    id: str
    user_id: str
    created_at: datetime
    messages: Optional[List[MessageRead]] = []

    class Config:
        from_attributes = True

class StreamRequest(BaseModel):
    message: str
    user_id: str
    chat_id: Optional[str] = None
    model: Optional[str] = None
    base64_image: Optional[str] = None
