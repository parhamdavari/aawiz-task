import httpx
from fastapi import HTTPException, status
from app.config import Settings


class SnapAuthClient:
    def __init__(self, settings: Settings):
        self.base_url = settings.snapauth_base_url.rstrip("/")
        self.api_key = settings.snapauth_api_key

    def _headers(self, token: str | None = None) -> dict[str, str]:
        if token:
            return {"Authorization": f"Bearer {token}"}
        if self.api_key:
            return {"Authorization": f"Bearer {self.api_key}"}
        return {}

    async def register_user(self, payload: dict) -> dict:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
            response = await client.post("/v1/users", json=payload, headers=self._headers())
        self._raise_for_status(response)
        return response.json()

    async def login(self, payload: dict) -> dict:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
            response = await client.post("/v1/auth/login", json=payload)
        self._raise_for_status(response)
        return response.json()

    async def refresh(self, payload: dict) -> dict:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
            response = await client.post("/v1/auth/refresh", json=payload)
        self._raise_for_status(response)
        return response.json()

    async def me(self, access_token: str) -> dict:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
            response = await client.get("/v1/auth/me", headers=self._headers(access_token))
        self._raise_for_status(response)
        return response.json()

    async def logout(self, payload: dict, access_token: str | None = None) -> dict:
        async with httpx.AsyncClient(base_url=self.base_url, timeout=10.0) as client:
            response = await client.post("/v1/auth/logout", json=payload, headers=self._headers(access_token))
        self._raise_for_status(response)
        return response.json()

    @staticmethod
    def _raise_for_status(response: httpx.Response) -> None:
        if response.status_code >= 400:
            try:
                detail = response.json()
            except Exception:
                detail = {"message": response.text}
            raise HTTPException(
                status_code=response.status_code,
                detail=detail,
            )

