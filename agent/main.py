"""Entry point for the TodoOrchestrator agent."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Dict, Optional

from .config import Config
from .observability import configure_logging, configure_tracing, get_logger, traced_span
from .todo_tool import TodoServiceTool


@dataclass
class Message:
    role: str
    content: str


class TodoOrchestrator:
    """A minimal Vertex ADK-like orchestrator with ReAct-style prompting."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self.tool = TodoServiceTool(
            base_url=config.todo_api_base_url,
            rate_limit_per_minute=config.rate_limit_per_minute,
            cache_ttl_seconds=config.cache_ttl_seconds,
        )
        self.logger = get_logger("agent")

    def _decide_action(self, message: str) -> Dict[str, str]:
        lowered = message.lower()
        if any(unsafe in lowered for unsafe in ["/rm", "drop table", "delete from"]):
            raise ValueError("Unsafe instruction detected. Please rephrase your request.")
        if "list" in lowered or "show" in lowered:
            return {"action": "list"}
        if "create" in lowered or "add" in lowered:
            return {"action": "create"}
        if "update" in lowered or "edit" in lowered:
            return {"action": "update"}
        if "delete" in lowered or "remove" in lowered:
            return {"action": "delete"}
        return {"action": "clarify"}

    def handle(self, message: Message) -> str:
        with traced_span("agent.handle", role=message.role):
            decision = self._decide_action(message.content)
            action = decision["action"]
            if action == "clarify":
                return "I can manage your todos (list, create, update, delete). What would you like to do?"
            try:
                if action == "list":
                    todos = self.tool.list_todos()
                    if not todos:
                        return "You have no todos yet. Want me to add one?"
                    return "Here are your todos:\n" + json.dumps(todos, indent=2)
                if action == "create":
                    payload = self._extract_payload(message.content)
                    created = self.tool.create_todo(payload)
                    return f"Created todo '{created['title']}' with id {created['id']}."
                if action == "update":
                    payload = self._extract_payload(message.content)
                    todo_id = payload.pop("id", None)
                    if not todo_id:
                        return "Please provide the todo id to update."
                    updated = self.tool.update_todo(todo_id, payload)
                    return f"Updated todo {updated['id']} to status {updated['status']}."
                if action == "delete":
                    todo_id = self._extract_id(message.content)
                    if not todo_id:
                        return "Please provide the todo id to delete."
                    deleted = self.tool.delete_todo(todo_id)
                    return f"Deleted todo {deleted.get('id', todo_id)}."
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.error("agent_error", error=str(exc))
                return "I ran into an error while processing your request. Please try again."
            return "I could not determine your intent."

    def _extract_payload(self, text: str) -> Dict[str, str]:
        payload: Dict[str, str] = {}
        patterns = {
            "title": r"title:\s*([^;]+)",
            "description": r"description:\s*([^;]+)",
            "status": r"status:\s*([^;]+)",
            "id": r"id:\s*([^;\s]+)",
        }
        for key, pattern in patterns.items():
            match = re.search(pattern, text, flags=re.IGNORECASE)
            if match:
                payload[key] = match.group(1).strip()
        if not payload.get("title"):
            payload["title"] = "Untitled"
        return payload

    def _extract_id(self, text: str) -> Optional[str]:
        match = re.search(r"id:\s*([^;\s]+)", text, flags=re.IGNORECASE)
        return match.group(1).strip() if match else None


def main() -> None:
    configure_logging()
    configure_tracing()
    config = Config.from_env()
    agent = TodoOrchestrator(config)
    logger = get_logger("cli")
    logger.info("todo_orchestrator_ready", base_url=config.todo_api_base_url)
    print("TodoOrchestrator is running. Type 'quit' to exit.")
    while True:
        user_input = input("You: ")
        if user_input.lower().strip() == "quit":
            break
        message = Message(role="user", content=user_input)
        reply = agent.handle(message)
        print(f"Agent: {reply}")


if __name__ == "__main__":
    main()
