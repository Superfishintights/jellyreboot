from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

security = HTTPBasic()

def get_credentials():
    username = os.getenv("JELLYREBOOT_USERNAME")
    password = os.getenv("JELLYREBOOT_PASSWORD")
    
    if not username or not password:
        raise Exception("Authentication credentials not properly configured. Please check environment variables.")
    
    return username, password

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    try:
        valid_username, valid_password = get_credentials()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Server configuration error"
        )

    is_correct_username = secrets.compare_digest(
        credentials.username.encode("utf8"),
        valid_username.encode("utf8")
    )
    is_correct_password = secrets.compare_digest(
        credentials.password.encode("utf8"),
        valid_password.encode("utf8")
    )
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username