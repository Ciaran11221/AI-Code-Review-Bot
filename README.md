# 🤖 AI Code Review Bot

A GitHub Actions bot that automatically reviews pull requests using Claude AI. 
Posts inline comments with severity labels directly on changed lines.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Claude](https://img.shields.io/badge/AI-Claude%20Haiku-orange)
![GitHub Actions](https://img.shields.io/badge/CI-GitHub%20Actions-2088FF)

---

## Features

- **Automatic PR reviews** — triggers on every pull request to `main`/`master`
- **Inline comments** — posts feedback directly on the relevant line, not just a generic summary
- **Severity labels** — 🔴 Critical / 🟡 Warning / 🟢 Suggestion
- **Category tagging** — Bug, Security, Performance, Style, Readability
- **Cost-efficient** — uses Claude Haiku, skips lock files and minified assets, caps diff size
- **Structured output** — Pydantic models ensure reliable, parseable LLM responses

## How It Works

```
PR opened → GitHub Actions triggers → Diff fetched & parsed
→ Changed lines sent to Claude API → Structured JSON review returned
→ Inline comments posted to PR → Summary with verdict posted
```

## Example Output

```
🔴 Critical 🔒 security
Hardcoded credentials detected on this line. Use environment variables
or a secrets manager instead.

Suggestion: password = os.environ["DB_PASSWORD"]
```

## Setup

### 1. Add your API key to GitHub Secrets

In your repo: **Settings → Secrets → Actions → New repository secret**

```
Name:  ANTHROPIC_API_KEY
Value: your-key-here
```

### 2. Copy the workflow file

```bash
mkdir -p .github/workflows
cp review.yml .github/workflows/review.yml
```

### 3. That's it

Open a pull request — the bot will review it automatically.

---

## Project Structure

```
ai-code-review-bot/
├── .github/workflows/
│   └── review.yml          # GitHub Actions workflow
├── reviewer/
│   ├── bot.py              # Main entrypoint
│   ├── diff_parser.py      # Parse git diffs into structured data
│   ├── claude_client.py    # Claude API integration
│   ├── github_client.py    # Post comments via GitHub API
│   └── models.py           # Pydantic schemas for structured output
├── tests/
│   └── test_diff_parser.py
├── .env.example
└── requirements.txt
```

## Cost

Typical costs using Claude Haiku:

| PR Size | Approx Cost |
|---------|-------------|
| Small (~50 changed lines) | ~$0.001 |
| Medium (~200 lines) | ~$0.003 |
| Large (~500 lines) | ~$0.007 |

Built with cost-efficiency in mind: lock files, minified assets, and images are automatically skipped.
The model is configurable — swap to `claude-sonnet` in `claude_client.py` for deeper analysis.

## Running Tests

```bash
pip install -r requirements.txt
pytest tests/ -v
```

## Tech Stack

- **Python 3.11**
- **Anthropic Claude API** (Haiku model)
- **PyGithub** — GitHub API client
- **Pydantic v2** — structured LLM output validation
- **GitHub Actions** — CI/CD trigger

---

Built as a portfolio project demonstrating AI integration, automation engineering, and GitHub Actions CI/CD.
