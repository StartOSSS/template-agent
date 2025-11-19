from typing import Any

import pytest
import responses
import requests

from agent.todo_tool import TodoServiceTool


@pytest.fixture
def todo_tool() -> TodoServiceTool:
    return TodoServiceTool(
        base_url="https://api.example.com", rate_limit_per_minute=5, cache_ttl_seconds=1
    )


def add_response(
    rsps: responses.RequestsMock, method: str, url: str, status: int, json_body: Any
) -> None:
    rsps.add(getattr(responses, method.upper()), url, json=json_body, status=status)


def test_list_todos_caches(todo_tool: TodoServiceTool) -> None:
    with responses.RequestsMock() as rsps:
        add_response(
            rsps,
            "GET",
            "https://api.example.com/todos",
            200,
            [{"id": "1", "title": "Test", "status": "open"}],
        )
        first = todo_tool.list_todos()
        second = todo_tool.list_todos()
    assert first == second


def test_create_todo_validates(todo_tool: TodoServiceTool) -> None:
    with responses.RequestsMock() as rsps:
        add_response(
            rsps,
            "POST",
            "https://api.example.com/todos",
            201,
            {"id": "2", "title": "Hello", "status": "open"},
        )
        created = todo_tool.create_todo({"title": "Hello"})
    assert created["id"] == "2"


def test_update_todo(todo_tool: TodoServiceTool) -> None:
    with responses.RequestsMock() as rsps:
        add_response(
            rsps,
            "PUT",
            "https://api.example.com/todos/2",
            200,
            {"id": "2", "title": "Hi", "status": "done"},
        )
        updated = todo_tool.update_todo("2", {"title": "Hi", "status": "done"})
    assert updated["status"] == "done"


def test_delete_todo(todo_tool: TodoServiceTool) -> None:
    with responses.RequestsMock() as rsps:
        add_response(
            rsps,
            "DELETE",
            "https://api.example.com/todos/2",
            200,
            {"id": "2", "title": "Hi", "status": "done"},
        )
        deleted = todo_tool.delete_todo("2")
    assert deleted["id"] == "2"


def test_rate_limit(todo_tool: TodoServiceTool) -> None:
    todo_tool.rate_limiter.tokens = 0
    with pytest.raises(RuntimeError):
        todo_tool.list_todos(use_cache=False)


def test_prompt_injection_guard(todo_tool: TodoServiceTool) -> None:
    with pytest.raises(ValueError):
        todo_tool.create_todo({"title": "DROP TABLE users;"})


def test_retry_on_500_succeeds(todo_tool: TodoServiceTool) -> None:
    with responses.RequestsMock() as rsps:
        add_response(
            rsps, "GET", "https://api.example.com/todos", 500, {"error": "boom"}
        )
        add_response(
            rsps,
            "GET",
            "https://api.example.com/todos",
            200,
            [{"id": "3", "title": "Recovered", "status": "open"}],
        )
        todos = todo_tool.list_todos(use_cache=False)
        assert len(rsps.calls) == 2
    assert todos[0]["title"] == "Recovered"


def test_400_errors_do_not_retry(todo_tool: TodoServiceTool) -> None:
    with responses.RequestsMock() as rsps:
        add_response(
            rsps, "POST", "https://api.example.com/todos", 400, {"error": "bad"}
        )
        with pytest.raises(requests.HTTPError):
            todo_tool.create_todo({"title": "Bad"})
        assert len(rsps.calls) == 1
