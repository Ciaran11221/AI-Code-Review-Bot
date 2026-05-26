import json
import os
import anthropic
from reviewer.diff_parser import FileDiff
from reviewer.models import ReviewComment, ReviewSummary

# Use Haiku for cost efficiency — still excellent for code review
MODEL = "claude-haiku-4-5-20251001"

SYSTEM_PROMPT = """You are a senior software engineer doing a code review. 
Your job is to find real issues — bugs, security problems, performance issues — 
not to nitpick style unless it genuinely matters.

Be direct and specific. If something is fine, don't comment on it.
Focus on: bugs, security vulnerabilities, performance issues, error handling gaps, 
and logic errors. Minor style suggestions are low priority.

You must respond with ONLY valid JSON matching this exact schema:
{
  "verdict": "approve" | "needs_changes" | "comment",
  "summary": "2-3 sentence overall summary",
  "comments": [
    {
      "file_path": "path/to/file.py",
      "line_number": 42,
      "severity": "critical" | "warning" | "suggestion",
      "category": "bug" | "security" | "performance" | "style" | "readability",
      "comment": "Clear explanation of the issue",
      "suggestion": "Optional: what to do instead, or null"
    }
  ],
  "critical_count": 0,
  "warning_count": 0,
  "suggestion_count": 0
}

Only include comments for genuine issues. An empty comments array is fine for clean code.
Do not include any text outside the JSON."""


def build_prompt(file_diffs: list[FileDiff], pr_title: str, pr_description: str) -> str:
    """Build the review prompt from parsed diffs."""
    sections = [
        f"PR Title: {pr_title}",
        f"PR Description: {pr_description or 'No description provided'}",
        "",
        "Changed files to review:",
        "",
    ]

    for diff in file_diffs:
        sections.append(f"### {diff.file_path} ({diff.language})")
        sections.append("```diff")
        sections.append(diff.raw_diff)
        sections.append("```")
        sections.append("")

    return "\n".join(sections)


def review_pr(
    file_diffs: list[FileDiff],
    pr_title: str,
    pr_description: str,
) -> ReviewSummary:
    """Send the diff to Claude and return a structured review."""
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    prompt = build_prompt(file_diffs, pr_title, pr_description)

    message = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_response = message.content[0].text

    # Strip any accidental markdown fences
    clean = raw_response.strip()
    if clean.startswith("```"):
        clean = "\n".join(clean.split("\n")[1:])
    if clean.endswith("```"):
        clean = "\n".join(clean.split("\n")[:-1])

    data = json.loads(clean.strip())

    # Parse comments
    comments = [ReviewComment(**c) for c in data.get("comments", [])]

    return ReviewSummary(
        verdict=data["verdict"],
        summary=data["summary"],
        comments=comments,
        critical_count=sum(1 for c in comments if c.severity == "critical"),
        warning_count=sum(1 for c in comments if c.severity == "warning"),
        suggestion_count=sum(1 for c in comments if c.severity == "suggestion"),
    )
