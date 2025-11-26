from typing import Any
from pydantic import BaseModel, Field, ConfigDict, field_validator


class UserBase(BaseModel):
    username: str
    full_name: str | None = None
    roles: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] | None = None


class UserCreate(UserBase):
    password: str

    def to_snapauth_payload(self) -> dict[str, Any]:
        """Convert to SnapAuth API format."""
        payload = {
            "username": self.username,
            "password": self.password,
            "roles": self.roles if self.roles else ["user"],
        }
        meta = self.metadata or {}
        if self.full_name:
            meta["full_name"] = self.full_name
        if meta:
            payload["metadata"] = meta
        return payload


class UserLogin(BaseModel):
    username: str
    password: str


class UserRead(BaseModel):
    id: str
    username: str
    full_name: str | None = None
    roles: list[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)

    @field_validator("roles", mode="before")
    @classmethod
    def parse_roles(cls, value: Any) -> list[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [role.strip() for role in value.split(",") if role.strip()]
        return list(value)

