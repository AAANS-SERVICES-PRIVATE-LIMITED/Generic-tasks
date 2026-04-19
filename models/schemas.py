from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class Recipient(BaseModel):
    email: str
    name: Optional[str] = None
    company: Optional[str] = None


class SendRequest(BaseModel):
    recipients: List[Recipient]
    subject: str
    html_body: str


class ManualSendRequest(BaseModel):
    email: str
    name: Optional[str] = None
    company: Optional[str] = None
    subject: str
    html_body: Optional[str] = None
    template_name: Optional[str] = None


class TemplateCreate(BaseModel):
    name: str = Field(..., example="Welcome Email")
    html_body: str = Field(..., example="<h1>Hello {{name}}</h1><p>Welcome to {{company}}</p>")
