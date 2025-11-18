import os
import tempfile

import pytest

from agent.config import Config


def test_config_from_env_validates_and_trims():
    with tempfile.NamedTemporaryFile() as creds:
        env = {
            "TODO_API_BASE_URL": "https://example.com/",
            "VERTEX_LOCATION": "europe-west4",
            "VERTEX_PROJECT_ID": "proj-123",
            "GOOGLE_APPLICATION_CREDENTIALS": creds.name,
            "MAX_CONTEXT_TOKENS": "4096",
            "RATE_LIMIT_PER_MINUTE": "15",
            "CACHE_TTL_SECONDS": "5",
        }
        with pytest.raises(KeyError):
            os.environ["SHOULD_NOT_EXIST"]
        for key, value in env.items():
            os.environ[key] = value
        cfg = Config.from_env()
        assert cfg.todo_api_base_url == "https://example.com"
        assert cfg.vertex_location == "europe-west4"
        assert cfg.vertex_project_id == "proj-123"
        assert cfg.google_application_credentials == creds.name
        assert cfg.max_context_tokens == 4096
        assert cfg.rate_limit_per_minute == 15
        assert cfg.cache_ttl_seconds == 5


def test_config_missing_url_raises():
    for key in list(os.environ.keys()):
        if key.startswith("TODO_API_BASE_URL"):
            os.environ.pop(key)
    with pytest.raises(ValueError):
        Config.from_env()
