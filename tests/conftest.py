import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import PostgresDsn

from domprozrachno.app import create_app
from domprozrachno.config import Settings

TEST_DSN = "postgresql://test:unused@localhost:1/test"


@pytest.fixture
def settings() -> Settings:
    return Settings(
        database_url=PostgresDsn(TEST_DSN),
        app_env="test",
        app_version="0.8.0-test",
        port=8080,
        log_level="info",
        _env_file=None,
    )


@pytest.fixture
def app(settings: Settings) -> FastAPI:
    return create_app(settings)


@pytest.fixture
def client(app: FastAPI) -> TestClient:
    return TestClient(app)
