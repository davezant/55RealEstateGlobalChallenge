import os
from datetime import datetime, timezone

from flask import Request, Response
from werkzeug.exceptions import Unauthorized, TooManyRequests
from sqlalchemy.orm import Session
from sqlalchemy import select, func, delete

from libs.security.hashing import verify_if_hash_correct, create_hash
from libs.security.jwt import create_access_token, decode_access_token, ACCESS_TOKEN_EXPIRE_SECONDS
from libs.security.throttle import login_throttle

from schemas.admin import UserLoginSchema, UserRegistrationSchema
from models.users import UserModel, RevokedTokenModel

COOKIE_NAME = "access-token"

DUMMY_HASH = create_hash("senha-inexistente")

def normalize_email(email: str) -> str:
    return email.strip().lower()

def authenticate_user(db: Session, request: UserLoginSchema, client_id: str = "") -> UserModel:
    email = normalize_email(request.email)
    throttle_key = f"{client_id}|{email}"

    if login_throttle.is_blocked(throttle_key):
        raise TooManyRequests(description="Muitas tentativas. Aguarde alguns minutos.")

    stmt = select(UserModel).where(UserModel.email == email)
    user: UserModel | None = db.scalar(stmt)

    raw_pwd = request.password.get_secret_value()
    hashed = user.hash_pwd if user and user.hash_pwd else None

    if not hashed:
        verify_if_hash_correct(raw_pwd, DUMMY_HASH)
    elif verify_if_hash_correct(raw_pwd, hashed):
        login_throttle.reset(throttle_key)
        return user

    login_throttle.register_failure(throttle_key)
    raise Unauthorized(description="Usuário ou senha incorretos")

def issue_token(user: UserModel) -> str:
    token_data = {"sub": str(user.user_id), "username": user.username, "email": user.email}
    return create_access_token(data=token_data)

def login_user(db: Session, request: UserLoginSchema, client_id: str = "") -> str:
    user = authenticate_user(db, request, client_id)
    return issue_token(user)

def create_user(db: Session, request: UserRegistrationSchema):
    pwd = request.password.get_secret_value()
    encrypted_password = create_hash(pwd)

    new_user = UserModel(
        username = request.username,
        role = request.role,
        email = normalize_email(request.email),
        hash_pwd = encrypted_password,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user

def get_total_users(db: Session) -> int:
    stmt = select(func.count(UserModel.user_id))
    
    total = db.scalar(stmt) or 0
    return total

def token_from_request(request: Request) -> str | None:
    token = request.cookies.get(COOKIE_NAME)

    if not token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]

    return token

def current_session(db: Session, request: Request) -> dict | None:
    token = token_from_request(request)
    if not token:
        return None

    payload = decode_access_token(token)
    if not payload or not payload.get("jti"):
        return None

    if db.get(RevokedTokenModel, payload["jti"]) is not None:
        return None

    return payload

def revoke_session(db: Session, request: Request) -> None:
    token = token_from_request(request)
    payload = decode_access_token(token) if token else None

    if not payload or not payload.get("jti"):
        return

    now = datetime.now(timezone.utc)
    db.execute(delete(RevokedTokenModel).where(RevokedTokenModel.expires_at < now))

    if db.get(RevokedTokenModel, payload["jti"]) is None:
        db.add(RevokedTokenModel(
            jti=payload["jti"],
            expires_at=datetime.fromtimestamp(payload["exp"], tz=timezone.utc),
        ))

    db.commit()

def attach_session_cookie(response: Response, token: str) -> Response:
    secure = os.getenv("COOKIE_SECURE", "false").lower() in ("true", "1")

    response.set_cookie(
        key=COOKIE_NAME,
        value=token,
        max_age=ACCESS_TOKEN_EXPIRE_SECONDS,
        httponly=True,
        samesite="Lax",
        secure=secure,
    )

    return response
