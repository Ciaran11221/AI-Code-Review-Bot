import os
from github import Github
from github.PullRequest import PullRequest
from reviewer.models import ReviewSummary

SEVERITY_EMOJI = {
    "critical": "🔴",
    "warning":  "🟡",
    "suggestion": "🟢",
}

CATEGORY_EMOJI = {
    "bug":         "🐛",
    "security":    "🔒",
    "performance": "⚡",
    "style":       "✨",
    "readability": "📖",
}

VERDICT_EMOJI = {
    "approve":       "✅",
    "needs_changes": "❌",
    "comment":       "💬",
}


def get_pull_request() -> PullRequest:
    """Get the PR object from environment variables set by GitHub Actions."""
    token = os.environ["GITHUB_TOKEN"]
    repo_name = os.environ["REPO_NAME"]
    pr_number = int(os.environ["PR_NUMBER"])

    g = Github(token)
    repo = g.get_repo(repo_name)
    return repo.get_pull(pr_number)


def get_pr_diff(pr: PullRequest) -> str:
    """Fetch the raw unified diff for the PR."""
    import urllib.request

    url = pr.diff_url
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"token {os.environ['GITHUB_TOKEN']}"},
    )
    with urllib.request.urlopen(req) as response:
        return response.read().decode("utf-8")


def post_review(pr: PullRequest, review: ReviewSummary) -> None:
    """Post the review summary and inline comments to GitHub."""

    # Build summary comment
    verdict_emoji = VERDICT_EMOJI[review.verdict]
    lines = [
        f"## {verdict_emoji} AI Code Review",
        "",
        review.summary,
        "",
        "| 🔴 Critical | 🟡 Warnings | 🟢 Suggestions |",
        "|------------|------------|----------------|",
        f"| {review.critical_count} | {review.warning_count} | {review.suggestion_count} |",
        "",
        "_Powered by Claude Haiku · [ai-code-review-bot](https://github.com/yourusername/ai-code-review-bot)_",
    ]

    summary_body = "\n".join(lines)

    # Build inline review comments for the GitHub review
    review_comments = []
    for c in review.comments:
        sev = SEVERITY_EMOJI[c.severity]
        cat = CATEGORY_EMOJI[c.category]
        body_parts = [
            f"{sev} **{c.severity.capitalize()}** {cat} `{c.category}`",
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

    # Determine GitHub review event
    if review.verdict == "approve":
        event = "APPROVE"
    elif review.verdict == "needs_changes":
        event = "REQUEST_CHANGES"
    else:
        event = "COMMENT"

    # Post as a single GitHub review (groups all inline comments together)
    pr.create_review(
        body=summary_body,
        event=event,
        comments=review_comments,
    )

    print(f"✅ Review posted: {event} with {len(review_comments)} inline comments")
