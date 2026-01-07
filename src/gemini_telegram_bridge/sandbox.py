from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class WorkspaceSandbox:
    root: Path

    def __post_init__(self) -> None:
        self.root = self.root.resolve()

    def resolve(self, raw_path: str | Path | None = None, *, current_project: Path | None = None) -> Path:
        if raw_path in (None, "", "."):
            base = current_project or self.root
            return base.resolve()

        candidate = Path(raw_path).expanduser()
        if candidate.is_absolute():
            resolved = candidate.resolve()
        else:
            start = current_project or self.root
            resolved = (start / candidate).resolve()

        if not self.is_safe(resolved):
            raise PermissionError(f"Path escapes WORKSPACE_ROOT: {resolved}")
        return resolved

    def is_safe(self, candidate: str | Path) -> bool:
        resolved = Path(candidate).resolve()
        return resolved == self.root or self.root in resolved.parents

    def safe_members(self, members: list[str]) -> None:
        for name in members:
            resolved = (self.root / name).resolve()
            if not self.is_safe(resolved):
                raise PermissionError(f"Archive member escapes WORKSPACE_ROOT: {name}")
