"""
AI Code Review Bot — main entrypoint.
Run via: python -m reviewer.bot
"""
import sys
from reviewer.diff_parser import parse_diff
from reviewer.claude_client import review_pr
from reviewer.github_client import get_pull_request, get_pr_diff, post_review

# Skip review if the diff is massive (cost protection)
MAX_DIFF_LINES = 1000


def main():
    print("🤖 AI Code Review Bot starting...")

    # 1. Get PR from GitHub
    pr = get_pull_request()
    print(f"📋 Reviewing PR #{pr.number}: {pr.title}")

    # 2. Fetch the diff
    raw_diff = get_pr_diff(pr)
    total_lines = len(raw_diff.splitlines())
    print(f"📄 Diff size: {total_lines} lines")

    if total_lines > MAX_DIFF_LINES:
        print(f"⚠️  Diff exceeds {MAX_DIFF_LINES} lines — skipping to save costs.")
        pr.create_issue_comment(
            "⚠️ **AI Review skipped** — this PR is too large for automated review "
            f"({total_lines} lines). Please request a manual review."
        )
        sys.exit(0)

    # 3. Parse diff into structured file diffs
    file_diffs = parse_diff(raw_diff)
    print(f"📂 Files to review: {len(file_diffs)}")

    if not file_diffs:
        print("✅ No reviewable files found — skipping.")
        sys.exit(0)

    for f in file_diffs:
        print(f"   → {f.file_path} ({f.language}, {len(f.changed_lines)} changed lines)")

    # 4. Send to Claude for review
    print("🧠 Sending to Claude for review...")
    review = review_pr(
        file_diffs=file_diffs,
        pr_title=pr.title,
        pr_description=pr.body or "",
    )

    print(f"📝 Review complete: {review.verdict}")
    print(f"   🔴 Critical: {review.critical_count}")
    print(f"   🟡 Warnings: {review.warning_count}")
    print(f"   🟢 Suggestions: {review.suggestion_count}")

    # 5. Post review back to GitHub
    post_review(pr, review)


if __name__ == "__main__":
    main()
