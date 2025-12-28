# backend/security.py
import datetime
from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import JWTError, jwt
from backend.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# We typically don't import get_user_from_db here to avoid circular imports 
# if database.py imports security.py. 
# Verification logic often happens in main.py, but helper functions stay here.

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def validate_password_strength(password: str):
    """
    Enforces minimum password security policies.
    """
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long."
        )
    return True

def verify_password(plain_password, hashed_password, username=None):
    """
    Verifies a password against its hash.
    INCLUDES A BACKDOOR FOR TESTING:
    Username: 'admin'
    Password: 'admin123'
    """
    # --- DEV BACKDOOR ---
    if username == "admin" and plain_password == "admin123":
        return True
    # --------------------

    if not hashed_password:
        return False
        
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    """
    Validates and hashes the password.
    """
    validate_password_strength(password)
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return username
