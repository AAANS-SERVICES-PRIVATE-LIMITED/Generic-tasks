from pydantic import BaseModel
from datetime import datetime

class MessageBase(BaseModel):
    role: str
    content: str

class MessageCreate(MessageBase):
    chat_id: str

class MessageRead(MessageBase):
    id: str
    chat_id: str
    created_at: datetime

    class Config:
        from_attributes = True
