"""Integration-style tests that exercise the orchestrator against a mocked Todo API."""

from __future__ import annotations

import json
from typing import Dict

import pytest
import responses

from agent.config import Config
from agent.main import Message, TodoOrchestrator


def build_agent(base_url: str) -> TodoOrchestrator:
    cfg = Config(
        todo_api_base_url=base_url,
        vertex_location="us-central1",
        vertex_project_id="demo",
        google_application_credentials=None,
        max_context_tokens=2048,
        rate_limit_per_minute=20,
        cache_ttl_seconds=0,
    )
    return TodoOrchestrator(cfg)


def add_json(rsps: responses.RequestsMock, method: str, url: str, status: int, payload: Dict) -> None:
    rsps.add(getattr(responses, method.upper()), url, status=status, json=payload)


@pytest.mark.e2e
@responses.activate
def test_end_to_end_crud_flow() -> None:
    base_url = "https://todo.example.test"
    agent = build_agent(base_url)

    add_json(responses, "POST", f"{base_url}/todos", 201, {"id": "1", "title": "New", "status": "open"})
    add_json(responses, "GET", f"{base_url}/todos", 200, [{"id": "1", "title": "New", "status": "open"}])
    add_json(
        responses,
        "PUT",
        f"{base_url}/todos/1",
        200,
        {"id": "1", "title": "New", "status": "done"},
    )
    add_json(responses, "DELETE", f"{base_url}/todos/1", 200, {"id": "1", "status": "done"})

    reply = agent.handle(Message(role="user", content="create todo title: New"))
    assert "Created todo" in reply

    reply = agent.handle(Message(role="user", content="list todos"))
    assert "Here are your todos" in reply
    assert json.loads(reply.split("\n", 1)[1])[0]["id"] == "1"

    reply = agent.handle(Message(role="user", content="update todo id:1 status: done"))
    assert "Updated todo" in reply

    reply = agent.handle(Message(role="user", content="delete todo id:1"))
    assert "Deleted todo" in reply

    assert len(responses.calls) == 4
