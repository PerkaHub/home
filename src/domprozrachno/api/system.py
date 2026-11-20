from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from ..config import Environment, Settings

router = APIRouter(tags=["system"])


class HealthResponse(BaseModel):
    status: Literal["ok"]


class VersionResponse(BaseModel):
    version: str
    environment: Environment


def app_settings(request: Request) -> Settings:
    return cast(Settings, request.app.state.settings)


@router.get("/health")
def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.get("/version")
def version(settings: Annotated[Settings, Depends(app_settings)]) -> VersionResponse:
    return VersionResponse(version=settings.app_version, environment=settings.app_env)
