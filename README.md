# 🤖 AI Code Review Bot

Automated code reviews on every pull request using Claude AI and GitHub Actions. Posts inline comments with severity labels directly on the changed lines — no manual review trigger needed.

![Python](https://img.shields.io/badge/Python-3.11+-blue) ![GitHub Actions](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF) ![Claude](https://img.shields.io/badge/AI-Claude%20Haiku-orange) ![Pydantic](https://img.shields.io/badge/Validation-Pydantic%20v2-red)

---

## What it does

When a pull request is opened or updated, the bot:

1. Fetches the PR diff via the GitHub API
2. Parses changed lines by file, filtering out lock files, minified assets, and images
3. Sends the diff to Claude via **tool use** (structured output — no JSON parsing, no hallucinated fields)
4. Posts inline review comments directly on the relevant lines
5. Submits a summary verdict: `approve`, `needs_changes`, or `comment`

If anything fails, it posts a clear error comment on the PR rather than silently dying.

## Example output

```
🔴 Critical 🔒 security
Hardcoded credentials detected. Use environment variables instead.

Suggestion: password = os.environ["DB_PASSWORD"]
```

```
🟡 Warning 🐛 bug
This function returns None if the list is empty but callers expect a list.

Suggestion: return result or []
```

## How it works

```
PR opened/updated
      ↓
GitHub Actions triggers
      ↓
Diff fetched & parsed (lock files, images skipped)
      ↓
Changed lines sent to Claude API via tool use
      ↓
Structured review returned (verdict + inline comments)
      ↓
Comments posted to PR · Summary verdict submitted
```

## Setup

### 1. Add your Anthropic API key to GitHub Secrets

In your repo: **Settings → Secrets and variables → Actions → New repository secret**

```
Name:  ANTHROPIC_API_KEY
Value: your-anthropic-api-key
```

The `GITHUB_TOKEN` is provided automatically by GitHub Actions — no extra setup needed.

### 2. Copy the workflow file

```bash
mkdir -p .github/workflows
cp review.yml .github/workflows/review.yml
```

### 3. Copy the reviewer package

```
reviewer/
├── __init__.py
├── bot.py
├── claude_client.py
├── diff_parser.py
├── github_client.py
└── models.py
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Open a pull request

The bot fires automatically. Check the **Actions** tab to watch it run, and the **Files changed** tab on your PR to see inline comments.

---

## Project structure

```
ai-code-review-bot/
├── .github/workflows/
│   └── review.yml          # GitHub Actions workflow (concurrency + pip caching)
├── reviewer/
│   ├── bot.py              # Entrypoint — orchestrates the review flow
│   ├── diff_parser.py      # Parses unified diffs into structured FileDiff objects
│   ├── claude_client.py    # Claude API integration via tool use
│   ├── github_client.py    # Posts reviews and comments via PyGitHub
│   └── models.py           # Pydantic models with computed severity counts
├── tests/
│   ├── test_diff_parser.py
│   ├── test_models.py
│   └── test_claude_client.py  # Mocked — runs without an API key
└── requirements.txt
```

## Running tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Design decisions

**Tool use instead of JSON prompting** — Claude is forced to call a `submit_review` tool with a defined schema. The SDK validates the output, so there's no manual JSON parsing or string stripping.

**Computed severity counts** — `critical_count`, `warning_count`, and `suggestion_count` are Pydantic `computed_field` properties derived from the comments list. They can never be out of sync.

**Graceful failure** — if the Claude API or GitHub API fails after retries, the bot posts a clear error comment on the PR rather than failing silently.

**Cost controls** — uses Claude Haiku, skips lock files and minified assets, caps diff size at 1000 lines, and the workflow uses `concurrency` to cancel stale runs when new commits are pushed.

## Cost

| PR size | Approx cost |
|---------|-------------|
| Small (~50 changed lines) | ~$0.001 |
| Medium (~200 lines) | ~$0.003 |
| Large (~500 lines) | ~$0.007 |

---

Built with Python, Claude Haiku, PyGitHub, Pydantic v2, and GitHub Actions.