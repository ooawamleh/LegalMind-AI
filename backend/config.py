# backend/config.py
import os
import logging
from dotenv import load_dotenv

# Load Environment Variables
load_dotenv()

# --- CONFIGURATION ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# Paths
UPLOAD_DIR = "secure_uploads"
DB_DIR = "chroma_db"
SQLITE_DB = "legal_AIagent.db"

# Create Directories
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(DB_DIR, exist_ok=True)

# --- LOGGING SETUP ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
audit_logger = logging.getLogger("audit")
audit_logger.propagate = False
audit_handler = logging.FileHandler('audit_trail.log')
audit_formatter = logging.Formatter('%(asctime)s | USER:%(user)s | ACTION:%(action)s | DETAILS:%(message)s')
audit_handler.setFormatter(audit_formatter)
audit_logger.addHandler(audit_handler)

def log_audit(user: str, action: str, details: str):
    audit_logger.info(details, extra={"user": user, "action": action})

if not OPENROUTER_API_KEY:
    logging.warning("⚠️ OPENROUTER_API_KEY is missing!")