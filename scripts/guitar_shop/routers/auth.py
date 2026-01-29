import hashlib
import secrets
import json
import base64
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from models import User, UserRole, UserCreate, UserLogin, UserResponse, TokenResponse
from database import DatabaseManager

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
security = HTTPBearer()


class AuthManager:
    SECRET_KEY = secrets.token_hex(32)
    TOKEN_EXPIRY_HOURS = 24
    
    @staticmethod
    def hash_password(password: str) -> str:
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}${password_hash}"
    
    @staticmethod
    def verify_password(password: str, stored_hash: str) -> bool:
        try:
            salt, hash_value = stored_hash.split('$')
            computed_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return computed_hash == hash_value
        except ValueError:
            return False
    
    @classmethod
    def generate_token(cls, user: User) -> str:
        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "user_id": user.id,
            "username": user.username,
            "role": user.role.value,
            "exp": (datetime.now() + timedelta(hours=cls.TOKEN_EXPIRY_HOURS)).isoformat()
        }
        
        header_b64 = base64.b64encode(json.dumps(header).encode()).decode()
        payload_b64 = base64.b64encode(json.dumps(payload).encode()).decode()
        
        signature_input = f"{header_b64}.{payload_b64}.{cls.SECRET_KEY}"
        signature = hashlib.sha256(signature_input.encode()).hexdigest()
        
        return f"{header_b64}.{payload_b64}.{signature}"
    
    @classmethod
    def verify_token(cls, token: str) -> Optional[dict]:
        try:
            parts = token.split('.')
            if len(parts) != 3:
                return None
            
            header_b64, payload_b64, signature = parts
            
            expected_signature = hashlib.sha256(
                f"{header_b64}.{payload_b64}.{cls.SECRET_KEY}".encode()
            ).hexdigest()
            
            if signature != expected_signature:
                return None
            
            payload = json.loads(base64.b64decode(payload_b64))
            
            exp = datetime.fromisoformat(payload['exp'])
            if datetime.now() > exp:
                return None
            
            return payload
            
        except Exception:
            return None
    
    @staticmethod
    def validate_password_strength(password: str) -> tuple:
        errors = []
        
        if len(password) < 6:
            errors.append("Password must be at least 6 characters")
        
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")
        
        if errors:
            return False, "; ".join(errors)
        
        return True, "Password is valid"
    
    @staticmethod
    def validate_email(email: str) -> bool:
        if not email or '@' not in email:
            return False
        parts = email.split('@')
        if len(parts) != 2:
            return False
        local, domain = parts
        if not local or not domain or '.' not in domain:
            return False
        return True


db = DatabaseManager("guitar_shop.db")


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    token = credentials.credentials
    payload = AuthManager.verify_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return payload


def get_admin_user(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user['role'] != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user


def get_customer_user(current_user: dict = Depends(get_current_user)) -> dict:
    if current_user['role'] == UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action is only available for customers"
        )
    return current_user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate):
    valid, message = AuthManager.validate_password_strength(user_data.password)
    if not valid:
        raise HTTPException(status_code=400, detail=message)
    
    if not AuthManager.validate_email(user_data.email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    if db.get_user_by_username(user_data.username):
        raise HTTPException(status_code=400, detail="Username already exists")
    
    if db.get_user_by_email(user_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=AuthManager.hash_password(user_data.password),
        role=UserRole.CUSTOMER
    )
    
    try:
        user_id = db.create_user(user)
        user.id = user_id
        return user
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
def login_user(credentials: UserLogin):
    user = db.get_user_by_username(credentials.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    if not AuthManager.verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    db.set_user_online(user.id, True)
    
    token = AuthManager.generate_token(user)
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=user
    )


@router.get("/me", response_model=UserResponse)
def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    user = db.get_user_by_id(current_user['user_id'])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/logout")
def logout_user(current_user: dict = Depends(get_current_user)):
    db.set_user_online(current_user['user_id'], False)
    return {"message": "Successfully logged out"}


__all__ = ['router', 'AuthManager', 'get_current_user', 'get_admin_user', 'get_customer_user']
