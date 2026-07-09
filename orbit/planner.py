from __future__ import annotations

from dataclasses import dataclass

from .project import ProjectInfo


@dataclass
class PlanStep:
    path: str
    reason: str


@dataclass
class Plan:
    objective: str
    steps: list[PlanStep]


class Planner:
    """
    Simple planner for ORBIT.

    Version 1 does not use AI.
    It only creates a basic execution plan.
    """

    def __init__(self, project: ProjectInfo) -> None:
        self.project = project

    def plan_edit(
        self,
        path: str,
        instruction: str,
    ) -> Plan:
        return Plan(
            objective=instruction,
            steps=[
                PlanStep(
                    path=path,
                    reason="Apply requested edit.",
                )
            ],
        )