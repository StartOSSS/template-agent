"""Configuration utilities for the Todo orchestrator agent."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Optional


_VALID_URL_RE = re.compile(r"^https?://[\w\.-]+(:\d+)?(/.*)?$")


@dataclass
class Config:
    """Dataclass capturing runtime configuration for the agent."""

    todo_api_base_url: str
    vertex_location: str
    vertex_project_id: str
    google_application_credentials: Optional[str]
    max_context_tokens: int
    rate_limit_per_minute: int
    cache_ttl_seconds: int

    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables with validation."""

        def getenv_str(key: str, default: str | None = None) -> str | None:
            value = os.environ.get(key, default)
            return value if value is None or isinstance(value, str) else str(value)

        def required_str(key: str) -> str:
            value = getenv_str(key)
            if not value:
                raise ValueError(f"{key} is required. Set the Todo API endpoint in the environment.")
            return value

        def bounded_int(key: str, default: int, *, positive: bool = True) -> int:
            raw = getenv_str(key, str(default))
            if raw is None:
                raw = str(default)
            try:
                parsed = int(raw)
            except ValueError as exc:
                raise ValueError(f"{key} must be an integer") from exc
            if positive and parsed <= 0:
                raise ValueError(f"{key} must be positive")
            if not positive and parsed < 0:
                raise ValueError(f"{key} must be non-negative")
            return parsed

        todo_api_base_url = required_str("TODO_API_BASE_URL")
        if not _VALID_URL_RE.match(todo_api_base_url):
            raise ValueError(f"TODO_API_BASE_URL '{todo_api_base_url}' is not a valid HTTP(S) URL.")

        vertex_location = getenv_str("VERTEX_LOCATION", "us-central1") or "us-central1"
        vertex_project_id = getenv_str("VERTEX_PROJECT_ID", "demo-project") or "demo-project"
        google_application_credentials = getenv_str("GOOGLE_APPLICATION_CREDENTIALS")

        max_context_tokens = bounded_int("MAX_CONTEXT_TOKENS", 8192)
        rate_limit_per_minute = bounded_int("RATE_LIMIT_PER_MINUTE", 30)
        cache_ttl_seconds = bounded_int("CACHE_TTL_SECONDS", 10, positive=False)

        if google_application_credentials and not os.path.isfile(google_application_credentials):
            raise ValueError(
                "GOOGLE_APPLICATION_CREDENTIALS points to a non-existent file. Provide a valid service account key."
            )

        return cls(
            todo_api_base_url=todo_api_base_url.rstrip("/"),
            vertex_location=vertex_location,
            vertex_project_id=vertex_project_id,
            google_application_credentials=google_application_credentials,
            max_context_tokens=max_context_tokens,
            rate_limit_per_minute=rate_limit_per_minute,
            cache_ttl_seconds=cache_ttl_seconds,
        )
