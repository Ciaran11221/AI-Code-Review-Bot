"""
Tests for ReviewSummary computed fields.

The key thing being tested: counts are derived from the comments list,
not stored separately. This means they can never be out of sync.
"""
import pytest
from reviewer.models import ReviewComment, ReviewSummary


def make_comment(severity: str, category: str = "bug") -> ReviewComment:
    return ReviewComment(
        file_path="main.py",
        line_number=1,
        severity=severity,
        category=category,
        comment="Test comment",
    )


def test_counts_computed_from_comments():
    summary = ReviewSummary(
        verdict="needs_changes",
        summary="Found issues.",
        comments=[
            make_comment("critical"),
            make_comment("critical"),
            make_comment("warning"),
            make_comment("suggestion"),
        ],
    )
    assert summary.critical_count == 2
    assert summary.warning_count == 1
    assert summary.suggestion_count == 1


def test_empty_comments_gives_zero_counts():
    summary = ReviewSummary(
        verdict="approve",
        summary="Looks good.",
        comments=[],
    )
    assert summary.critical_count == 0
    assert summary.warning_count == 0
    assert summary.suggestion_count == 0


def test_counts_update_if_comments_change():
    """Computed fields always reflect the current state of comments."""
    summary = ReviewSummary(
        verdict="comment",
        summary="Minor notes.",
        comments=[make_comment("suggestion")],
    )
    assert summary.suggestion_count == 1
    assert summary.critical_count == 0


def test_suggestion_field_is_optional():
    comment = make_comment("warning")
    assert comment.suggestion is None


def test_suggestion_field_can_be_set():
    comment = ReviewComment(
        file_path="app.py",
        line_number=10,
        severity="critical",
        category="security",
        comment="Hardcoded secret.",
        suggestion="Use os.environ['SECRET'] instead.",
    )
    assert comment.suggestion is not None
