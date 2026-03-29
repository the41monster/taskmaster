import os
import jwt
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional, cast
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from taskmaster import models, database

SECRET_KEY_RAW = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

if not SECRET_KEY_RAW:
    raise RuntimeError("SECRET_KEY environment variable is required")

SECRET_KEY: str = SECRET_KEY_RAW

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire, "jti": str(uuid.uuid4())})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_token_payload(token: str):
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def is_token_revoked(db: Session, token: str, payload: Optional[dict] = None) -> bool:
    token_hash = hash_token(token)
    if db.query(models.RevokedToken).filter(models.RevokedToken.token_hash == token_hash).first():
        return True

    if payload:
        jti = payload.get("jti")
        if jti and db.query(models.RevokedToken).filter(models.RevokedToken.jti == jti).first():
            return True

    return False


def revoke_token(db: Session, token: str, payload: dict, user_id: str) -> models.RevokedToken:
    revoked = models.RevokedToken(
        token_hash=hash_token(token),
        jti=payload.get("jti", str(uuid.uuid4())),
        user_id=user_id,
        expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
    )
    db.add(revoked)
    db.commit()
    db.refresh(revoked)
    return revoked

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)):
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = cast(dict[str, Any], get_token_payload(token))
        username = payload.get("sub")
        if username is None:
            raise credential_exception
    except jwt.PyJWTError:
        raise credential_exception

    if is_token_revoked(db, token, payload):
        raise credential_exception
    
    user =  db.query(models.User).filter(models.User.username == username).first()
    if user is None:
        raise credential_exception
    if not bool(cast(Any, user.is_active)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return user