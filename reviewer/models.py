from pydantic import BaseModel, computed_field
from typing import Literal


class ReviewComment(BaseModel):
    """A single inline review comment on a specific line."""
    file_path: str
    line_number: int
    severity: Literal["critical", "warning", "suggestion"]
    category: Literal["bug", "security", "performance", "style", "readability"]
    comment: str
    suggestion: str | None = None  # Optional code fix suggestion


class ReviewSummary(BaseModel):
    """Overall PR review summary with auto-computed severity counts."""
    verdict: Literal["approve", "needs_changes", "comment"]
    summary: str
    comments: list[ReviewComment]

    # Computed from comments — never out of sync, never wrong
    @computed_field
    @property
    def critical_count(self) -> int:
        return sum(1 for c in self.comments if c.severity == "critical")

    @computed_field
    @property
    def warning_count(self) -> int:
        return sum(1 for c in self.comments if c.severity == "warning")

    @computed_field
    @property
    def suggestion_count(self) -> int:
        return sum(1 for c in self.comments if c.severity == "suggestion")
