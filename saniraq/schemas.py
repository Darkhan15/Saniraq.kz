from pydantic import BaseModel
from datetime import datetime

class UserCreate(BaseModel):
    username: str
    password: str
    name: str
    city: str
    phone: str

class UserUpdate(BaseModel):
    name: str
    city: str
    phone: str

class AdCreate(BaseModel):
    type: str
    price: float
    adress: str
    area: float
    rooms_count: int
    description: str

class CommentCreate(BaseModel):
    content: str
    created_at: datetime

class CommentUpdate(BaseModel):
    content: str
