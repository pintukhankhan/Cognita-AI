from __future__ import annotations
import inspect
from typing import Any, Callable, Dict, List
from pydantic import BaseModel
import structlog

logger = structlog.get_logger(__name__)


class ToolMeta(BaseModel):
    name: str; description: str; parameters: Dict[str, Any]


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, func: Callable, description: str, parameters: Dict[str, Any]) -> None:
        self._tools[name] = {"fn": func, "meta": ToolMeta(name=name, description=description, parameters=parameters)}
        logger.info("cognita.tool.registered", name=name)

    def list_tools(self) -> List[ToolMeta]:
        return [t["meta"] for t in self._tools.values()]

    def names(self) -> List[str]:
        return list(self._tools.keys())

    async def execute(self, name: str, **kwargs) -> Any:
        if name not in self._tools:
            raise ValueError(f"unknown tool {name}")
        fn = self._tools[name]["fn"]
        return await fn(**kwargs) if inspect.iscoroutinefunction(fn) else fn(**kwargs)


async def calculator(expression: str) -> float:
    allowed = set("0123456789+-*/.() ")
    if not set(expression) <= allowed:
        raise ValueError("unsafe expression")
    return float(eval(expression, {"__builtins__": {}}, {}))


async def web_search(query: str, num_results: int = 3) -> List[Dict[str, str]]:
    return [{"title": f"Result {i + 1}", "snippet": f"Stub snippet for: {query}"} for i in range(num_results)]


default_registry = ToolRegistry()
default_registry.register("calculator", calculator, "Evaluate a math expression", {"expression": "string"})
default_registry.register("web_search", web_search, "Search the web", {"query": "string", "num_results": "int"})
