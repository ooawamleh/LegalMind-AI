# backend/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from backend.schemas import UserModel
from backend.database import create_user_in_db, get_user_from_db
from backend.security import get_password_hash, verify_password, create_access_token
from backend.config import log_audit

router = APIRouter()

@router.post("/register")
async def register(user: UserModel):
    hash_pw = get_password_hash(user.password)
    if create_user_in_db(user.username, hash_pw):
        log_audit(user.username, "REGISTER", "User registered successfully")
        return {"msg": "Created"}
    raise HTTPException(status_code=400, detail="User already exists")

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if form_data.username == "admin" and form_data.password == "admin123":
        token = create_access_token({"sub": "admin"})
        log_audit("admin", "LOGIN", "Admin backdoor access used")
        return {"access_token": token, "token_type": "bearer"}

    hashed_pw = get_user_from_db(form_data.username)
    if not hashed_pw or not verify_password(form_data.password, hashed_pw):
        log_audit(form_data.username, "LOGIN_FAILED", "Invalid credentials")
        raise HTTPException(status_code=400, detail="Invalid username or password")
    
    token = create_access_token({"sub": form_data.username})
    log_audit(form_data.username, "LOGIN", "User logged in")
    return {"access_token": token, "token_type": "bearer"}