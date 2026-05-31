import os
import time
import anthropic
from reviewer.diff_parser import FileDiff
from reviewer.models import ReviewComment, ReviewSummary

MODEL = "claude-haiku-4-5-20251001"
MAX_RETRIES = 2

SYSTEM_PROMPT = """You are a senior software engineer doing a thorough code review.
Find real issues: bugs, security vulnerabilities, performance problems, error handling gaps.
Be direct and specific. If code is clean, say so — don't manufacture feedback.
Only comment on genuine problems. An empty comments list is a valid and good result."""

# Tool schema — Claude is forced to call this, guaranteeing structured output.
# No JSON parsing, no string stripping, no hallucinated fields.
REVIEW_TOOL = {
    "name": "submit_review",
    "description": "Submit the completed code review with all findings.",
    "input_schema": {
        "type": "object",
        "properties": {
            "verdict": {
                "type": "string",
                "enum": ["approve", "needs_changes", "comment"],
                "description": "approve=no issues, needs_changes=blocking issues found, comment=non-blocking feedback only",
            },
            "summary": {
                "type": "string",
                "description": "2-3 sentence overall summary of the PR quality.",
            },
            "comments": {
                "type": "array",
                "description": "Inline comments on specific lines. Empty array if no issues found.",
                "items": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                        "line_number": {"type": "integer"},
                        "severity": {"type": "string", "enum": ["critical", "warning", "suggestion"]},
                        "category": {"type": "string", "enum": ["bug", "security", "performance", "style", "readability"]},
                        "comment": {"type": "string", "description": "Clear explanation of the issue."},
                        "suggestion": {"type": "string", "description": "Optional: what to do instead."},
                    },
                    "required": ["file_path", "line_number", "severity", "category", "comment"],
                },
            },
        },
        "required": ["verdict", "summary", "comments"],
    },
}


def build_prompt(file_diffs: list[FileDiff], pr_title: str, pr_description: str) -> str:
    sections = [
        f"PR Title: {pr_title}",
        f"PR Description: {pr_description or 'No description provided.'}",
        "",
        "Changed files:",
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
    """
    Send the diff to Claude via tool use and return a structured ReviewSummary.

    Using tool_choice={"type": "tool", "name": "submit_review"} forces Claude
    to call the tool rather than respond in free text — the SDK validates the
    schema, so we never need to parse or sanitise JSON manually.
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    prompt = build_prompt(file_diffs, pr_title, pr_description)

    for attempt in range(MAX_RETRIES + 1):
        try:
            message = client.messages.create(
                model=MODEL,
                max_tokens=2048,
                system=SYSTEM_PROMPT,
                tools=[REVIEW_TOOL],
                tool_choice={"type": "tool", "name": "submit_review"},
                messages=[{"role": "user", "content": prompt}],
            )

            # With tool_choice forced, the first content block is always the tool call
            tool_use_block = next(
                block for block in message.content if block.type == "tool_use"
            )
            data = tool_use_block.input  # Already a dict — no JSON parsing needed

            comments = [ReviewComment(**c) for c in data.get("comments", [])]
            return ReviewSummary(
                verdict=data["verdict"],
                summary=data["summary"],
                comments=comments,
            )

        except Exception as e:
            if attempt < MAX_RETRIES:
                wait = 2 ** attempt  # exponential backoff: 1s, 2s
                print(f"⚠️  Claude API attempt {attempt + 1} failed ({e}) — retrying in {wait}s")
                time.sleep(wait)
            else:
                raise
