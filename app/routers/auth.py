from fastapi import APIRouter, Depends
from pydantic import BaseModel
from fastapi.security import HTTPAuthorizationCredentials

from app.config import Settings, get_settings
from app.dependencies.auth import AuthenticatedUser, get_current_user, security
from app.schemas.user import UserCreate, UserLogin, UserRead
from app.services.snapauth import SnapAuthClient


class RefreshRequest(BaseModel):
    refresh_token: str


class LogoutRequest(BaseModel):
    refresh_token: str


def get_snapauth_client(settings: Settings = Depends(get_settings)) -> SnapAuthClient:
    return SnapAuthClient(settings)


router = APIRouter()


@router.post("/register", response_model=dict)
async def register_user(
    user: UserCreate,
    client: SnapAuthClient = Depends(get_snapauth_client),
):
    payload = user.to_snapauth_payload()
    return await client.register_user(payload)


@router.post("/login", response_model=dict)
async def login_user(
    credentials: UserLogin,
    client: SnapAuthClient = Depends(get_snapauth_client),
):
    return await client.login(credentials.model_dump())


@router.post("/refresh", response_model=dict)
async def refresh_token(
    body: RefreshRequest,
    client: SnapAuthClient = Depends(get_snapauth_client),
):
    return await client.refresh(body.model_dump())


@router.get("/me", response_model=dict)
async def read_current_user(
    auth: AuthenticatedUser = Depends(get_current_user),
    auth_header: HTTPAuthorizationCredentials = Depends(security),
    client: SnapAuthClient = Depends(get_snapauth_client),
):
    if auth_header:
        try:
            return await client.me(auth_header.credentials)
        except Exception:
            # If SnapAuth is unreachable, return cached user info.
            return UserRead.model_validate(auth.user).model_dump()
    return UserRead.model_validate(auth.user).model_dump()


@router.post("/logout", response_model=dict)
async def logout_user(
    body: LogoutRequest,
    auth_header: HTTPAuthorizationCredentials = Depends(security),
    client: SnapAuthClient = Depends(get_snapauth_client),
):
    access_token = auth_header.credentials if auth_header else None
    return await client.logout(body.model_dump(), access_token)
