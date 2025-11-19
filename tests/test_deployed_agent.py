"""Optional evaluation test that exercises a deployed agent endpoint."""

from __future__ import annotations

import os
from typing import Any, Dict

import pytest
import requests


DEPLOYED_URL = os.getenv("DEPLOYED_AGENT_URL")
DEPLOYED_TOKEN = os.getenv("DEPLOYED_AGENT_TOKEN")


def _headers() -> Dict[str, str]:
    if DEPLOYED_TOKEN:
        return {"Authorization": f"Bearer {DEPLOYED_TOKEN}"}
    return {}


def _extract_reply(payload: Any) -> str:
    if isinstance(payload, str):
        return payload
    if isinstance(payload, dict):
        if "reply" in payload:
            return str(payload["reply"])
        if "text" in payload:
            return str(payload["text"])
        # Vertex Agent Engine proxy may return predictions list
        predictions = payload.get("predictions")
        if (
            isinstance(predictions, list)
            and predictions
            and isinstance(predictions[0], dict)
        ):
            candidate = predictions[0].get("content") or predictions[0].get(
                "candidates"
            )
            if isinstance(candidate, list) and candidate:
                first = candidate[0]
                if isinstance(first, dict) and "output_text" in first:
                    return str(first["output_text"])
    return str(payload)


@pytest.mark.deployed
@pytest.mark.skipif(not DEPLOYED_URL, reason="DEPLOYED_AGENT_URL not configured")
def test_deployed_agent_handles_create_and_list() -> None:
    assert DEPLOYED_URL is not None

    create_resp = requests.post(
        DEPLOYED_URL,
        json={"query": "create todo title: e2e from pytest"},
        headers=_headers(),
        timeout=30,
    )
    create_resp.raise_for_status()
    create_reply = _extract_reply(
        create_resp.json()
        if create_resp.headers.get("content-type", "").startswith("application/json")
        else create_resp.text
    )
    assert "create" in create_reply.lower()

    list_resp = requests.post(
        DEPLOYED_URL,
        json={"query": "list todos"},
        headers=_headers(),
        timeout=30,
    )
    list_resp.raise_for_status()
    list_reply = _extract_reply(
        list_resp.json()
        if list_resp.headers.get("content-type", "").startswith("application/json")
        else list_resp.text
    )
    assert (
        any(word in list_reply.lower() for word in ["todo", "item", "list"])
        or "[" in list_reply
    )
