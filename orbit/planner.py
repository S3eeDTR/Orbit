from __future__ import annotations

from dataclasses import dataclass

from .chat import ChatSession
from .project import ProjectInfo
from .project_map import ProjectMap


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
    Hybrid planner for ORBIT.

    Uses AI first, then falls back to filename heuristics.
    """

    def __init__(
        self,
        project: ProjectInfo,
        chat: ChatSession,
        project_map: ProjectMap,
    ) -> None:
        self.project = project
        self.chat = chat
        self.project_map = project_map

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
        ai_plan = self.plan_with_ai(request)

        if ai_plan.steps:
            return ai_plan

        return self.plan_with_heuristics(request)

    def plan_with_ai(
        self,
        request: str,
        limit: int = 80,
    ) -> Plan:
        entries = self.project_map.build(limit)

        files = "\n\n".join(
            f"{entry.path}\nDescription: {entry.description}"
            for entry in entries
        )

        prompt = f"""
            You are ORBIT's planning engine.

            Your ONLY job is to decide which files must be modified to complete the user's request.

            User request:
            {request}

            Project files:
            {files}

            Instructions:

            - Select the smallest practical set of files, usually 1-3 files.
            - Return at most 3 files unless the request clearly requires more.
            - Include ONLY files that require code changes.
            - Do NOT include files that are merely related.
            - Prefer precision over completeness.
            - If a change can be made in one file, return one file.
            - Only return multiple files when they are all required.
            - Never invent file paths.
            - Use only the files listed above.

            Output format:
            One file path per line.

            Do not explain.
            Do not use markdown.
            Do not use bullets.
            Return nothing if no suitable file exists.
            """

        reply = self.chat.complete_once(prompt)

        if not reply:
            return Plan(objective=request, steps=[])

        selected = self._parse_file_paths(reply)

        steps = [
            PlanStep(
                path=path,
                reason="Selected by AI planner.",
            )
            for path in selected
        ]

        return Plan(
            objective=request,
            steps=steps,
        )

    def plan_with_heuristics(
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

    def _parse_file_paths(self, text: str) -> list[str]:
        valid_files = set(self.project.files)
        selected: list[str] = []

        for line in text.splitlines():
            path = line.strip().strip("-*` ")

            if path in valid_files and path not in selected:
                selected.append(path)

        return selected

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