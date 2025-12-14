# backend/schemas.py
from pydantic import BaseModel

class UserModel(BaseModel):
    username: str
    password: str

class QueryRequest(BaseModel):
    query: str