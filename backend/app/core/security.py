import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy.orm import Session

from app.db.models import AdminUser
from app.db.session import get_db

_basic_auth = HTTPBasic()


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode(), password_hash.encode())
    except ValueError:
        return False


def get_current_admin(
    credentials: HTTPBasicCredentials = Depends(_basic_auth),
    db: Session = Depends(get_db),
) -> AdminUser:
    user = db.query(AdminUser).filter_by(email=credentials.username).first()
    if user is None or user.password_hash is None or not verify_password(
        credentials.password, user.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return user
