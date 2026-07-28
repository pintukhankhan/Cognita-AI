from __future__ import annotations
from enum import Enum
from typing import Dict, List
import structlog
from src.agents.orchestrator import AgentOrchestrator

logger = structlog.get_logger(__name__)


class Role(Enum):
    RESEARCHER = "researcher"; WRITER = "writer"; REVIEWER = "reviewer"


_INSTR = {
    Role.RESEARCHER: "Gather facts objectively and cite sources.",
    Role.WRITER: "Synthesize into clear, well-structured prose.",
    Role.REVIEWER: "Check accuracy and completeness; suggest fixes.",
}


class MultiAgentOrchestrator:
    def __init__(self):
        self.agents: Dict[Role, AgentOrchestrator] = {}

    def register(self, role: Role, agent: AgentOrchestrator) -> None:
        self.agents[role] = agent

    async def run_workflow(self, session_id: str, task: str, workflow: List[Role]) -> str:
        current = task
        for role in workflow:
            prompt = f"{_INSTR[role]}\n\nTask:\n{current}"
            res = await self.agents[role].process_message(f"{session_id}_{role.value}", None, prompt)
            current = res["response"]
        return current
