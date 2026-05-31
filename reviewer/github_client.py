import os
import urllib.request
from github import Github
from github.PullRequest import PullRequest
from reviewer.models import ReviewSummary

SEVERITY_EMOJI = {"critical": "🔴", "warning": "🟡", "suggestion": "🟢"}
CATEGORY_EMOJI = {"bug": "🐛", "security": "🔒", "performance": "⚡", "style": "✨", "readability": "📖"}
VERDICT_EMOJI = {"approve": "✅", "needs_changes": "❌", "comment": "💬"}


def get_pull_request() -> PullRequest:
    """Get the PR from env vars injected by GitHub Actions."""
    g = Github(os.environ["GITHUB_TOKEN"])
    repo = g.get_repo(os.environ["REPO_NAME"])
    return repo.get_pull(int(os.environ["PR_NUMBER"]))


def get_pr_diff(pr: PullRequest) -> str:
    """Fetch the raw unified diff for the PR."""
    req = urllib.request.Request(
        pr.diff_url,
        headers={"Authorization": f"token {os.environ['GITHUB_TOKEN']}"},
    )
    with urllib.request.urlopen(req) as response:
        return response.read().decode("utf-8")


def post_review(pr: PullRequest, review: ReviewSummary) -> None:
    """Post summary + inline comments to GitHub as a single review."""
    repo_name = os.environ.get("REPO_NAME", "")
    repo_url = f"https://github.com/{repo_name}" if repo_name else ""

    lines = [
        f"## {VERDICT_EMOJI[review.verdict]} AI Code Review",
        "",
        review.summary,
        "",
        "| 🔴 Critical | 🟡 Warnings | 🟢 Suggestions |",
        "|------------|------------|----------------|",
        f"| {review.critical_count} | {review.warning_count} | {review.suggestion_count} |",
        "",
        f"_Powered by Claude Haiku · [ai-code-review-bot]({repo_url})_",
    ]

    review_comments = []
    for c in review.comments:
        body_parts = [
            f"{SEVERITY_EMOJI[c.severity]} **{c.severity.capitalize()}** {CATEGORY_EMOJI[c.category]} `{c.category}`",
            "",
            c.comment,
        ]
        if c.suggestion:
            body_parts += ["", f"**Suggestion:** {c.suggestion}"]

        review_comments.append({
            "path": c.file_path,
            "line": c.line_number,
            "body": "\n".join(body_parts),
        })

    event = {"approve": "APPROVE", "needs_changes": "REQUEST_CHANGES", "comment": "COMMENT"}[review.verdict]

    pr.create_review(
        body="\n".join(lines),
        event=event,
        comments=review_comments,
    )
    print(f"✅ Review posted: {event} with {len(review_comments)} inline comments")


def post_error_comment(pr: PullRequest, error: Exception) -> None:
    """Post a fallback comment when the review fails, rather than silently dying."""
    pr.create_issue_comment(
        f"⚠️ **AI Code Review failed**\n\n"
        f"`{type(error).__name__}: {error}`\n\n"
        "Please request a manual review."
    )
