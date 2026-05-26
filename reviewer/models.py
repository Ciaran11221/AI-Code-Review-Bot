from pydantic import BaseModel
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
    """Overall PR review summary."""
    verdict: Literal["approve", "needs_changes", "comment"]
    summary: str
    comments: list[ReviewComment]
    critical_count: int
    warning_count: int
    suggestion_count: int
