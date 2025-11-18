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

        def getenv(key: str, default: Optional[str] = None) -> Optional[str]:
            return os.environ.get(key, default)

        todo_api_base_url = getenv("TODO_API_BASE_URL")
        if not todo_api_base_url:
            raise ValueError("TODO_API_BASE_URL is required. Set the Todo API endpoint in the environment.")
        if not _VALID_URL_RE.match(todo_api_base_url):
            raise ValueError(f"TODO_API_BASE_URL '{todo_api_base_url}' is not a valid HTTP(S) URL.")

        vertex_location = getenv("VERTEX_LOCATION", "us-central1")
        vertex_project_id = getenv("VERTEX_PROJECT_ID", "demo-project")
        google_application_credentials = getenv("GOOGLE_APPLICATION_CREDENTIALS")

        max_context_tokens_raw = getenv("MAX_CONTEXT_TOKENS", "8192")
        try:
            max_context_tokens = int(max_context_tokens_raw)
        except ValueError as exc:
            raise ValueError("MAX_CONTEXT_TOKENS must be an integer") from exc
        if max_context_tokens <= 0:
            raise ValueError("MAX_CONTEXT_TOKENS must be positive")

        rate_limit_raw = getenv("RATE_LIMIT_PER_MINUTE", "30")
        try:
            rate_limit_per_minute = int(rate_limit_raw)
        except ValueError as exc:
            raise ValueError("RATE_LIMIT_PER_MINUTE must be an integer") from exc
        if rate_limit_per_minute <= 0:
            raise ValueError("RATE_LIMIT_PER_MINUTE must be positive")

        cache_ttl_raw = getenv("CACHE_TTL_SECONDS", "10")
        try:
            cache_ttl_seconds = int(cache_ttl_raw)
        except ValueError as exc:
            raise ValueError("CACHE_TTL_SECONDS must be an integer") from exc
        if cache_ttl_seconds < 0:
            raise ValueError("CACHE_TTL_SECONDS must be non-negative")

        credentials = google_application_credentials
        if credentials and not os.path.isfile(credentials):
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
