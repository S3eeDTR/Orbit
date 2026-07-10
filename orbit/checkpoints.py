from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .editor import EditProposal, Editor


@dataclass
class CheckpointFile:
    path: str
    original_content: str
    final_content: str


@dataclass
class Checkpoint:
    id: str
    created_at: str
    instruction: str
    files: list[CheckpointFile]
    undone: bool = False
    undone_at: str | None = None


class CheckpointManager:
    """Persist successful edits and restore them transactionally."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root).resolve()
        self.directory = self.root / ".orbit" / "checkpoints"
        self.directory.mkdir(parents=True, exist_ok=True)

    def save(
        self,
        instruction: str,
        proposals: list[EditProposal],
        editor: Editor,
    ) -> Checkpoint:
        """Save original and final contents after a successful workflow."""

        files = [
            CheckpointFile(
                path=proposal.path,
                original_content=proposal.original_content,
                final_content=editor.read_file(proposal.path),
            )
            for proposal in proposals
        ]

        checkpoint = Checkpoint(
            id=self._new_id(),
            created_at=datetime.now(timezone.utc).isoformat(),
            instruction=instruction.strip(),
            files=files,
        )

        self._write(checkpoint)
        return checkpoint

    def list(self, limit: int = 20) -> list[Checkpoint]:
        """Return checkpoints from newest to oldest."""

        checkpoints: list[Checkpoint] = []

        for path in self.directory.glob("*.json"):
            try:
                checkpoints.append(self._read_path(path))
            except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
                continue

        checkpoints.sort(key=lambda item: item.created_at, reverse=True)
        return checkpoints[:limit]

    def get(self, checkpoint_id: str) -> Checkpoint:
        """Resolve a complete or unique checkpoint ID prefix."""

        checkpoint_id = checkpoint_id.strip()
        if not checkpoint_id:
            raise ValueError("Checkpoint ID is required.")

        matches = [
            checkpoint
            for checkpoint in self.list(limit=10_000)
            if checkpoint.id == checkpoint_id
            or checkpoint.id.startswith(checkpoint_id)
        ]

        if not matches:
            raise ValueError(f"Checkpoint not found: {checkpoint_id}")

        if len(matches) > 1:
            raise ValueError(
                f"Checkpoint ID is ambiguous: {checkpoint_id}"
            )

        return matches[0]

    def latest_active(self) -> Checkpoint:
        """Return the newest checkpoint that has not already been undone."""

        for checkpoint in self.list(limit=10_000):
            if not checkpoint.undone:
                return checkpoint

        raise ValueError("No active checkpoints are available to undo.")

    def undo(
        self,
        editor: Editor,
        checkpoint_id: str | None = None,
    ) -> Checkpoint:
        """Restore one checkpoint transactionally and mark it undone."""

        checkpoint = (
            self.get(checkpoint_id)
            if checkpoint_id
            else self.latest_active()
        )

        if checkpoint.undone:
            raise ValueError(
                f"Checkpoint {checkpoint.id} has already been undone."
            )

        restore_proposals: list[EditProposal] = []

        for item in checkpoint.files:
            current_content = editor.read_file(item.path)
            restore_proposals.append(
                EditProposal(
                    path=item.path,
                    original_content=current_content,
                    new_content=item.original_content,
                    diff="",
                )
            )

        editor.apply_proposals(restore_proposals)

        checkpoint.undone = True
        checkpoint.undone_at = datetime.now(timezone.utc).isoformat()
        self._write(checkpoint)
        return checkpoint

    def _new_id(self) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        return f"{timestamp}-{uuid4().hex[:8]}"

    def _path(self, checkpoint_id: str) -> Path:
        return self.directory / f"{checkpoint_id}.json"

    def _write(self, checkpoint: Checkpoint) -> None:
        path = self._path(checkpoint.id)
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(asdict(checkpoint), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        temporary.replace(path)

    def _read_path(self, path: Path) -> Checkpoint:
        payload = json.loads(path.read_text(encoding="utf-8"))
        files = [CheckpointFile(**item) for item in payload.pop("files")]
        return Checkpoint(files=files, **payload)
