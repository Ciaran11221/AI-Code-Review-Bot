"""
Tests for claude_client — mocked so they run without an API key.

Why mock? We're not testing whether Claude returns good reviews.
We're testing that our code correctly handles the tool use response
and maps it to a ReviewSummary. The API call itself is Anthropic's concern.
"""
from unittest.mock import MagicMock, patch
import pytest
from reviewer.claude_client import review_pr
from reviewer.diff_parser import FileDiff


SAMPLE_FILE_DIFF = FileDiff(
    file_path="app.py",
    language="Python",
    changed_lines=[(5, 'password = "hunter2"')],
    raw_diff='@@ -4,1 +5,1 @@\n+    password = "hunter2"',
)

MOCK_ENV = {"ANTHROPIC_API_KEY": "test-key-not-real"}


def make_mock_tool_response(verdict, summary, comments):
    """Build a fake Anthropic SDK response that looks like a tool use block."""
    tool_block = MagicMock()
    tool_block.type = "tool_use"
    tool_block.input = {"verdict": verdict, "summary": summary, "comments": comments}
    message = MagicMock()
    message.content = [tool_block]
    return message


@patch.dict("os.environ", MOCK_ENV)
@patch("reviewer.claude_client.anthropic.Anthropic")
def test_review_pr_returns_summary(mock_anthropic):
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    mock_client.messages.create.return_value = make_mock_tool_response(
        verdict="needs_changes",
        summary="Hardcoded credentials found.",
        comments=[{
            "file_path": "app.py",
            "line_number": 5,
            "severity": "critical",
            "category": "security",
            "comment": "Hardcoded password detected.",
            "suggestion": "Use environment variables.",
        }],
    )

    result = review_pr(file_diffs=[SAMPLE_FILE_DIFF], pr_title="Add auth", pr_description="")

    assert result.verdict == "needs_changes"
    assert result.critical_count == 1
    assert result.warning_count == 0
    assert len(result.comments) == 1
    assert result.comments[0].category == "security"


@patch.dict("os.environ", MOCK_ENV)
@patch("reviewer.claude_client.anthropic.Anthropic")
def test_review_pr_approve_no_comments(mock_anthropic):
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    mock_client.messages.create.return_value = make_mock_tool_response(
        verdict="approve", summary="Clean change.", comments=[]
    )

    result = review_pr(file_diffs=[SAMPLE_FILE_DIFF], pr_title="Refactor", pr_description="")

    assert result.verdict == "approve"
    assert result.critical_count == 0
    assert result.comments == []


@patch.dict("os.environ", MOCK_ENV)
@patch("reviewer.claude_client.time.sleep")  # Prevent actual sleeping in tests
@patch("reviewer.claude_client.anthropic.Anthropic")
def test_review_pr_retries_on_failure(mock_anthropic, mock_sleep):
    """Verify retry logic fires before eventually raising."""
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    mock_client.messages.create.side_effect = Exception("API timeout")

    with pytest.raises(Exception):
        review_pr(file_diffs=[SAMPLE_FILE_DIFF], pr_title="Test", pr_description="")

    # Should have tried MAX_RETRIES + 1 = 3 times total
    assert mock_client.messages.create.call_count == 3
    # Should have slept between retries (exponential backoff)
    assert mock_sleep.call_count == 2
