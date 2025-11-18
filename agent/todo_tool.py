"""Tool adapter for the Todo REST API."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import backoff
import requests
from requests import Response

from .observability import emit_metric, get_logger, traced_span

_ALLOWED_STATUS = {"open", "in_progress", "done"}


@dataclass
class TodoItem:
    id: str
    title: str
    description: str
    status: str


class RateLimiter:
    """Simple token-bucket rate limiter."""

    def __init__(self, rate_per_minute: int) -> None:
        self.capacity = rate_per_minute
        self.tokens = rate_per_minute
        self.last_refill = time.monotonic()

    def allow(self) -> bool:
        now = time.monotonic()
        elapsed = now - self.last_refill
        if elapsed > 60:
            refill = int(elapsed // 60) * self.capacity
            self.tokens = min(self.capacity, self.tokens + refill)
            self.last_refill = now
        if self.tokens > 0:
            self.tokens -= 1
            return True
        return False


class TodoServiceTool:
    """A tool that talks to the Todo HTTP service."""

    def __init__(self, base_url: str, rate_limit_per_minute: int = 30, cache_ttl_seconds: int = 10) -> None:
        self.base_url = base_url.rstrip("/")
        self.logger = get_logger("todo_tool")
        self.rate_limiter = RateLimiter(rate_limit_per_minute)
        self.cache_ttl_seconds = cache_ttl_seconds
        self._cache: Optional[Tuple[float, List[Dict[str, Any]]]] = None

    def _ensure_rate_limit(self) -> None:
        if not self.rate_limiter.allow():
            emit_metric("rate_limit_exceeded", 1)
            raise RuntimeError("Rate limit exceeded. Please retry in a moment.")

    def _sanitize(self, text: str) -> str:
        lowered = text.lower()
        if any(token in lowered for token in ["/rm", "drop table", "delete from", "--"]):
            raise ValueError("Input rejected due to unsafe content.")
        return text.strip()[:500]

    def _validate_payload(self, data: Dict[str, Any]) -> Dict[str, Any]:
        title = self._sanitize(str(data.get("title", "")).strip())
        if not title:
            raise ValueError("title is required")
        description = self._sanitize(str(data.get("description", "")).strip()) if data.get("description") else ""
        status = data.get("status", "open")
        if status not in _ALLOWED_STATUS:
            raise ValueError(f"status must be one of {_ALLOWED_STATUS}")
        return {"title": title, "description": description, "status": status}

    def _normalize(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": payload.get("id") or payload.get("ID"),
            "title": payload.get("title"),
            "description": payload.get("description", ""),
            "status": payload.get("status", "open"),
        }

    def _request(self, method: str, path: str, **kwargs: Any) -> Response:
        self._ensure_rate_limit()
        url = f"{self.base_url}{path}"
        self.logger.info("tool_call_start", tool_name=method, url=url)
        with traced_span(f"todo.{method}", url=url):
            response = self._execute_request(method, url, **kwargs)
            latency = response.elapsed.total_seconds() * 1000 if response.elapsed else None
            self.logger.info(
                "tool_call_complete",
                tool_name=method,
                url=url,
                status_code=response.status_code,
                latency_ms=latency,
            )
            emit_metric("todo_tool_call", 1, method=method, status=str(response.status_code))
            return response

    @backoff.on_exception(
        backoff.expo,
        requests.HTTPError,
        max_time=8,
        giveup=lambda e: 400 <= e.response.status_code < 500,
    )
    def _execute_request(self, method: str, url: str, **kwargs: Any) -> Response:  # pragma: no cover - wrapped by backoff
        response = requests.request(method=method.upper(), url=url, timeout=10, **kwargs)
        response.raise_for_status()
        return response

    def list_todos(self, use_cache: bool = True) -> List[Dict[str, Any]]:
        if use_cache and self._cache:
            timestamp, cached = self._cache
            if time.time() - timestamp < self.cache_ttl_seconds:
                return cached
        response = self._request("get", "/todos")
        todos = [self._normalize(item) for item in response.json()]
        self._cache = (time.time(), todos)
        return todos

    def create_todo(self, data: Dict[str, Any]) -> Dict[str, Any]:
        payload = self._validate_payload(data)
        response = self._request("post", "/todos", json=payload)
        self._cache = None
        return self._normalize(response.json())

    def update_todo(self, todo_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        payload = self._validate_payload(data)
        response = self._request("put", f"/todos/{self._sanitize(todo_id)}", json=payload)
        self._cache = None
        return self._normalize(response.json())

    def delete_todo(self, todo_id: str) -> Dict[str, Any]:
        response = self._request("delete", f"/todos/{self._sanitize(todo_id)}")
        self._cache = None
        return self._normalize(response.json())

