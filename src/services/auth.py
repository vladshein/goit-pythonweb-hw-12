from datetime import datetime, timedelta, UTC
from typing import Optional

from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
import redis
import pickle

from src.db.connection import get_db
from src.db.models import UserRole
from src.schemas.contacts import User

from src.conf.config import settings
from src.services.users import UserService


class Hash:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password, hashed_password):
        """
        Verify a password against a hashed password.

        Args:
            plain_password (str): The password to verify.
            hashed_password (str): The hashed password to verify against.

        Returns:
            bool: Whether the password matches the hashed password.
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        """
        Hash a password for storing.

        Args:
            password (str): The password to hash.

        Returns:
            str: The hashed password.
        """
        return self.pwd_context.hash(password)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
redis_client = redis.Redis(host="localhost", port=6379, db=0)


# define a function to generate a new access token
async def create_access_token(data: dict, expires_delta: Optional[int] = None):
    """
    Generate a new access token.

    Args:
        data (dict): The data to be encoded in the token.
        expires_delta (Optional[int]): The number of seconds until the token expires.

    Returns:
        str: The encoded JWT token.

    If expires_delta is not provided, the token will expire after the number of seconds
    specified in the JWT_EXPIRATION_SECONDS setting.

    :raises jwt.JWTError: If there is an error generating the token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + timedelta(seconds=expires_delta)
    else:
        expire = datetime.now(UTC) + timedelta(seconds=settings.JWT_EXPIRATION_SECONDS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    """
    Get the current user based on the provided JWT token.

    Args:
        token (str): The JWT token to validate.
        db (Session): The database session to use.

    Returns:
        User: The current user.

    Raises:
        HTTPException: If the token is invalid or the user is not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode JWT
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        username = payload["sub"]
        if username is None:
            raise credentials_exception
    except JWTError as e:
        raise credentials_exception
    user_service = UserService(db)
    user = redis_client.get(f"username:{username}")
    if user is None:
        print("No user in redis, get it from db")
        user = await user_service.get_user_by_username(username)
        if user is None:
            raise credentials_exception
        redis_client.set(f"username:{username}", pickle.dumps(user), ex=600)
    else:
        print("Getting user from redis")
        user = pickle.loads(user)
    return user


def create_email_token(data: dict):
    """
    Create a JWT token for email verification.

    Args:
        data (dict): The data to be encoded in the token.

    Returns:
        str: The encoded JWT token.

    The token will expire after 7 days.

    :raises jwt.JWTError: If there is an error generating the token.
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=7)
    to_encode.update({"iat": datetime.now(UTC), "exp": expire})
    token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token


async def get_email_from_token(token: str):
    """
    Get the email address from a JWT token for email verification.

    Args:
        token (str): The JWT token to decode.

    Returns:
        str: The email address encoded in the token.

    Raises:
        HTTPException: If the token is invalid or the email address is not found.
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        email = payload["sub"]
        return email
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Невірний токен для перевірки електронної пошти",
        )


# Залежності для перевірки ролей
async def get_current_moderator_user(current_user: User = Depends(get_current_user)):
    """
    Get the current user if the user is a moderator or an administrator.

    This function is a dependency for routes that require the user to be a moderator or an administrator.

    Raises:
        HTTPException: If the user is not a moderator or an administrator.
    """
    if current_user.role not in [UserRole.MODERATOR, UserRole.ADMIN]:
        raise HTTPException(status_code=403, detail="Недостатньо прав доступу")
    return current_user


async def get_current_admin_user(current_user: User = Depends(get_current_user)):
    """
    Get the current user if the user is an administrator.

    This function is a dependency for routes that require the user to be an administrator.

    Raises:
        HTTPException: If the user is not an administrator.
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Недостатньо прав доступу")
    return current_user
