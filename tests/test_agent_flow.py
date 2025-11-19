from typing import Dict

from agent.config import Config
from agent.main import Message, TodoOrchestrator


class DummyTool:
    def __init__(self) -> None:
        self.calls: Dict[str, Dict[str, str]] = {}

    def list_todos(self, use_cache: bool = True):
        self.calls["list"] = {}
        return [{"id": "1", "title": "Test", "status": "open"}]

    def create_todo(self, data: Dict[str, str]):
        self.calls["create"] = data
        return {"id": "2", **data}

    def update_todo(self, todo_id: str, data: Dict[str, str]):
        self.calls["update"] = {"id": todo_id, **data}
        return {"id": todo_id, **data}

    def delete_todo(self, todo_id: str):
        self.calls["delete"] = {"id": todo_id}
        return {"id": todo_id}


def build_agent() -> TodoOrchestrator:
    cfg = Config(
        todo_api_base_url="https://example.com",
        vertex_location="us-central1",
        vertex_project_id="project",
        google_application_credentials=None,
        max_context_tokens=1024,
        rate_limit_per_minute=10,
        cache_ttl_seconds=1,
    )
    agent = TodoOrchestrator(cfg)
    agent.tool = DummyTool()  # type: ignore[assignment]
    return agent


def test_agent_lists_todos():
    agent = build_agent()
    reply = agent.handle(Message(role="user", content="list todos"))
    assert "Here are your todos" in reply
    assert "list" in agent.tool.calls


def test_agent_creates_todo():
    agent = build_agent()
    reply = agent.handle(Message(role="user", content="create todo title: New"))
    assert "Created todo" in reply
    assert agent.tool.calls["create"]["title"] == "New"


def test_agent_updates_todo():
    agent = build_agent()
    reply = agent.handle(Message(role="user", content="update todo id:1 status: done"))
    assert "Updated todo" in reply
    assert agent.tool.calls["update"]["id"] == "1"


def test_agent_needs_id_for_delete():
    agent = build_agent()
    reply = agent.handle(Message(role="user", content="delete todo"))
    assert "provide the todo id" in reply
