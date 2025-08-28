"""
Message Schemas
Phase 2: Backend Enhancement

Pydantic schemas for message and notification API endpoints
"""

import uuid
from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserInfo(BaseModel):
    id: uuid.UUID
    email: EmailStr

    class Config:
        orm_mode = True

class MessageBase(BaseModel):
    subject: str
    body: str


class MessageCreate(MessageBase):
    recipient_id: uuid.UUID


class MessageRead(MessageBase):
    id: uuid.UUID
    sender: UserInfo
    recipient: UserInfo
    is_read: bool
    is_starred: bool
    created_at: datetime

    class Config:
        orm_mode = True

class MessageUpdate(BaseModel):
    is_read: bool | None = None
    is_starred: bool | None = None



