from datetime import datetime, timedelta
from typing import Any

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


ALGORITHM = "HS256"


def create_access_token(subject: str | Any, expires_delta: timedelta) -> str:
    """
    Generates an access token using the given subject and expires delta time. It
    encodes the token using a secret key and a chosen algorithm, resulting in a
    secure and unique token.

    Args:
        subject (str | Any): identity of the user or application requesting an
            access token, which is included in the JWT as a claims object.
        expires_delta (timedelta): duration of time that the access token will be
            valid, and is used to calculate the expiration timestamp for the JWT
            encoded in the function.

    Returns:
        str: a JWT token containing an expiration date and subject ID.

    """
    expire = datetime.utcnow() + expires_delta
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)
