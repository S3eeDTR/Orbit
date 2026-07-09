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
    Planner for ORBIT.

    Performs simple heuristic searches over the indexed project
    to find relevant files.
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

    def plan_request(
        self,
        request: str,
    ) -> Plan:
        candidates = self.find_candidate_files(request)

        steps = [
            PlanStep(
                path=path,
                reason="Filename matches request.",
            )
            for path in candidates
        ]

        return Plan(
            objective=request,
            steps=steps,
        )

    def find_candidate_files(
        self,
        request: str,
        limit: int = 5,
    ) -> list[str]:
        words = {
            word.lower()
            for word in request.replace(".", " ").split()
            if len(word) >= 2
        }

        matches: list[tuple[int, str]] = []

        for path in self.project.files:
            score = self._score_path(path, words)

            if score > 0:
                matches.append((score, path))

        matches.sort(reverse=True)

        return [
            path
            for _, path in matches[:limit]
        ]

    def _score_path(
        self,
        path: str,
        words: set[str],
    ) -> int:
        path_lower = path.lower()
        filename = path_lower.split("/")[-1]
        stem = filename.rsplit(".", 1)[0]

        score = 0

        for word in words:
            if word == stem:
                score += 50
            elif word in stem:
                score += 20
            elif word in filename:
                score += 10
            elif word in path_lower:
                score += 5

        return score