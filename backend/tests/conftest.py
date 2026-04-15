from __future__ import annotations

import asyncio
import json
import sys
from collections.abc import Generator
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.db.base import Base
from backend.app.db.session import get_db_session
from backend.app.main import app


@dataclass
class ASGIResponse:
    status_code: int
    body: bytes

    def json(self) -> Any:
        return json.loads(self.body.decode("utf-8"))


class ASGITestClient:
    def __init__(self, app_instance) -> None:
        self.app = app_instance

    def get(self, path: str) -> ASGIResponse:
        return self.request("GET", path)

    def post(self, path: str, json: dict, headers: Optional[Dict[str, str]] = None) -> ASGIResponse:
        return self.request("POST", path, json_body=json, headers=headers)

    def patch(self, path: str, json: dict, headers: Optional[Dict[str, str]] = None) -> ASGIResponse:
        return self.request("PATCH", path, json_body=json, headers=headers)

    def request(
        self,
        method: str,
        path: str,
        json_body: Optional[dict] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> ASGIResponse:
        body = b""
        raw_headers = [(b"host", b"testserver")]

        if json_body is not None:
            body = json.dumps(json_body).encode("utf-8")
            raw_headers.append((b"content-type", b"application/json"))
        if headers is not None:
            raw_headers.extend((key.lower().encode("utf-8"), value.encode("utf-8")) for key, value in headers.items())

        async def run_request() -> ASGIResponse:
            request_sent = False
            messages: list[dict] = []

            async def receive() -> dict:
                nonlocal request_sent
                if request_sent:
                    return {"type": "http.disconnect"}
                request_sent = True
                return {"type": "http.request", "body": body, "more_body": False}

            async def send(message: dict) -> None:
                messages.append(message)

            scope = {
                "type": "http",
                "asgi": {"version": "3.0"},
                "http_version": "1.1",
                "method": method,
                "headers": raw_headers,
                "scheme": "http",
                "path": path,
                "raw_path": path.encode("utf-8"),
                "query_string": b"",
                "server": ("testserver", 80),
                "client": ("testclient", 50000),
                "root_path": "",
            }

            await self.app(scope, receive, send)

            status_code = 500
            response_body = b""
            for message in messages:
                if message["type"] == "http.response.start":
                    status_code = message["status"]
                elif message["type"] == "http.response.body":
                    response_body += message.get("body", b"")

            return ASGIResponse(status_code=status_code, body=response_body)

        return asyncio.run(run_request())


class StubEmailService:
    def __init__(self, *, should_fail: bool = False) -> None:
        self.should_fail = should_fail
        self.calls: list[dict[str, str]] = []
        self.approval_calls: list[dict[str, str]] = []
        self.pending_notifications: list[dict[str, str]] = []

    def send_welcome_email(
        self,
        to_email: str,
        full_name: str,
        username: str,
        temporary_password: str,
    ) -> bool:
        self.calls.append(
            {
                "to_email": to_email,
                "full_name": full_name,
                "username": username,
                "temporary_password": temporary_password,
            }
        )
        if self.should_fail:
            return False
        return True

    def send_registration_approved_email(
        self,
        to_email: str,
        full_name: str,
        username: str,
    ) -> bool:
        self.approval_calls.append(
            {
                "to_email": to_email,
                "full_name": full_name,
                "username": username,
            }
        )
        if self.should_fail:
            return False
        return True

    def send_pending_registration_notification(
        self,
        to_email: str,
        requester_name: str,
        requester_email: str,
        requester_username: str,
        requester_profile: str,
    ) -> bool:
        self.pending_notifications.append(
            {
                "to_email": to_email,
                "requester_name": requester_name,
                "requester_email": requester_email,
                "requester_username": requester_username,
                "requester_profile": requester_profile,
            }
        )
        if self.should_fail:
            return False
        return True


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        future=True,
    )
    TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, class_=Session)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


@pytest.fixture
def email_service() -> StubEmailService:
    return StubEmailService()


@pytest.fixture
def client(db_session: Session, email_service: StubEmailService) -> Generator[ASGITestClient, None, None]:
    async def override_get_db_session() -> Generator[Session, None, None]:
        yield db_session

    async def override_get_email_service() -> StubEmailService:
        return email_service

    app.dependency_overrides[get_db_session] = override_get_db_session
    from backend.app.services.email_service import get_email_service

    app.dependency_overrides[get_email_service] = override_get_email_service

    yield ASGITestClient(app)

    app.dependency_overrides.clear()
