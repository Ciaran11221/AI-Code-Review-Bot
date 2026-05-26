import re
from dataclasses import dataclass

# File extensions to skip — no value reviewing these
SKIP_EXTENSIONS = {
    ".lock", ".sum", ".mod",           # dependency lock files
    ".png", ".jpg", ".jpeg", ".gif",   # images
    ".svg", ".ico", ".woff", ".woff2", # assets
    ".min.js", ".min.css",             # minified files
}

# Files to skip by name
SKIP_FILENAMES = {
    "package-lock.json",
    "yarn.lock",
    "poetry.lock",
    "Pipfile.lock",
    "composer.lock",
    ".env.example",
    "CHANGELOG.md",
}

# Max lines of diff to send per file (cost control)
MAX_LINES_PER_FILE = 200


@dataclass
class FileDiff:
    file_path: str
    language: str
    changed_lines: list[tuple[int, str]]  # (line_number, line_content)
    raw_diff: str


def should_skip_file(file_path: str) -> bool:
    """Return True if the file should be excluded from review."""
    filename = file_path.split("/")[-1]

    if filename in SKIP_FILENAMES:
        return True

    for ext in SKIP_EXTENSIONS:
        if file_path.endswith(ext):
            return True

    return False


def detect_language(file_path: str) -> str:
    """Detect programming language from file extension."""
    ext_map = {
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".jsx": "React/JSX",
        ".tsx": "React/TSX",
        ".java": "Java",
        ".go": "Go",
        ".rs": "Rust",
        ".rb": "Ruby",
        ".php": "PHP",
        ".cs": "C#",
        ".cpp": "C++",
        ".c": "C",
        ".sh": "Shell",
        ".yml": "YAML",
        ".yaml": "YAML",
        ".tf": "Terraform",
        ".sql": "SQL",
    }
    for ext, lang in ext_map.items():
        if file_path.endswith(ext):
            return lang
    return "Unknown"


def parse_diff(raw_diff: str) -> list[FileDiff]:
    """
    Parse a unified git diff into structured FileDiff objects.
    Only extracts added/changed lines (+) — not removed lines.
    """
    file_diffs = []
    current_file = None
    current_lines = []
    current_raw = []
    line_number = 0

    for line in raw_diff.splitlines():
        # New file section
        if line.startswith("diff --git"):
            # Save previous file
            if current_file and current_lines:
                file_diffs.append(FileDiff(
                    file_path=current_file,
                    language=detect_language(current_file),
                    changed_lines=current_lines[:MAX_LINES_PER_FILE],
                    raw_diff="\n".join(current_raw),
                ))
            current_file = None
            current_lines = []
            current_raw = [line]
            line_number = 0

        elif line.startswith("+++ b/"):
            current_file = line[6:]  # strip '+++ b/'
            current_raw.append(line)

        elif line.startswith("@@ "):
            # Extract starting line number from hunk header e.g. @@ -10,4 +10,6 @@
            match = re.search(r"\+(\d+)", line)
            if match:
                line_number = int(match.group(1)) - 1
            current_raw.append(line)

        elif line.startswith("+") and not line.startswith("+++"):
            line_number += 1
            current_lines.append((line_number, line[1:]))  # strip leading +
            current_raw.append(line)

        elif line.startswith("-") and not line.startswith("---"):
            current_raw.append(line)  # keep in raw but don't count line number

        else:
            line_number += 1
            current_raw.append(line)

    # Save last file
    if current_file and current_lines:
        file_diffs.append(FileDiff(
            file_path=current_file,
            language=detect_language(current_file),
            changed_lines=current_lines[:MAX_LINES_PER_FILE],
            raw_diff="\n".join(current_raw),
        ))

    # Filter out files we should skip
    return [f for f in file_diffs if not should_skip_file(f.file_path)]
