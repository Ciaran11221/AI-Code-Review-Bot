"""
AI Code Review GUI — FastAPI backend
Run: uvicorn main:app --reload
"""
import os
import json
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import anthropic

app = FastAPI(title="AI Code Reviewer", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MODEL = "claude-haiku-4-5-20251001"

SYSTEM_PROMPT = """You are a senior software engineer doing a thorough code review.
Find real issues: bugs, security vulnerabilities, performance problems, error handling gaps, logic errors.
Be direct and specific. Only comment on genuine issues — don't nitpick if code is fine.

Respond ONLY with valid JSON, no markdown, no preamble:
{
  "verdict": "approve" | "needs_changes" | "comment",
  "summary": "2-3 sentence overall summary",
  "comments": [
    {
      "line_number": 42,
      "severity": "critical" | "warning" | "suggestion",
      "category": "bug" | "security" | "performance" | "style" | "readability",
      "comment": "Clear explanation of the issue",
      "suggestion": "What to do instead, or null"
    }
  ],
  "critical_count": 0,
  "warning_count": 0,
  "suggestion_count": 0
}"""


class ReviewRequest(BaseModel):
    code: str
    language: str
    filename: Optional[str] = "untitled"


class ReviewComment(BaseModel):
    line_number: int
    severity: str
    category: str
    comment: str
    suggestion: Optional[str] = None


class ReviewResponse(BaseModel):
    filename: str
    verdict: str
    summary: str
    comments: list[ReviewComment]
    critical_count: int
    warning_count: int
    suggestion_count: int


def call_claude(code: str, language: str, filename: str) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="ANTHROPIC_API_KEY not set")

    client = anthropic.Anthropic(api_key=api_key)

    prompt = f"""Review this {language} code from file: {filename}

```{language.lower()}
{code}
```"""

    message = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    if raw.startswith("```"):
        raw = "\n".join(raw.split("\n")[1:])
    if raw.endswith("```"):
        raw = "\n".join(raw.split("\n")[:-1])

    return json.loads(raw.strip())


@app.post("/review", response_model=ReviewResponse)
async def review_code(request: ReviewRequest):
    """Review pasted code."""
    if len(request.code.strip()) < 10:
        raise HTTPException(status_code=400, detail="Code is too short to review")

    data = call_claude(request.code, request.language, request.filename)
    comments = [ReviewComment(**c) for c in data.get("comments", [])]

    return ReviewResponse(
        filename=request.filename,
        verdict=data["verdict"],
        summary=data["summary"],
        comments=comments,
        critical_count=sum(1 for c in comments if c.severity == "critical"),
        warning_count=sum(1 for c in comments if c.severity == "warning"),
        suggestion_count=sum(1 for c in comments if c.severity == "suggestion"),
    )


@app.post("/review/upload", response_model=list[ReviewResponse])
async def review_files(files: list[UploadFile] = File(...)):
    """Review multiple uploaded files."""
    if len(files) > 10:
        raise HTTPException(status_code=400, detail="Max 10 files at once")

    LANGUAGE_MAP = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
        ".jsx": "React/JSX", ".tsx": "React/TSX", ".java": "Java",
        ".go": "Go", ".rs": "Rust", ".rb": "Ruby", ".php": "PHP",
        ".cs": "C#", ".cpp": "C++", ".c": "C", ".sh": "Shell",
        ".sql": "SQL", ".tf": "Terraform",
    }

    SKIP_EXTENSIONS = {".lock", ".png", ".jpg", ".gif", ".svg", ".min.js", ".min.css"}

    results = []
    for file in files:
        filename = file.filename or "untitled"
        ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

        if ext in SKIP_EXTENSIONS:
            continue

        content = await file.read()
        try:
            code = content.decode("utf-8")
        except UnicodeDecodeError:
            continue

        if len(code.strip()) < 10:
            continue

        language = LANGUAGE_MAP.get(ext, "Unknown")
        data = call_claude(code, language, filename)
        comments = [ReviewComment(**c) for c in data.get("comments", [])]

        results.append(ReviewResponse(
            filename=filename,
            verdict=data["verdict"],
            summary=data["summary"],
            comments=comments,
            critical_count=sum(1 for c in comments if c.severity == "critical"),
            warning_count=sum(1 for c in comments if c.severity == "warning"),
            suggestion_count=sum(1 for c in comments if c.severity == "suggestion"),
        ))

    return results


@app.get("/health")
def health():
    return {"status": "ok"}
