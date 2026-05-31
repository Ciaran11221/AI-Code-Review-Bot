import re
from dataclasses import dataclass

SKIP_EXTENSIONS = {
    ".lock", ".sum", ".mod",
    ".png", ".jpg", ".jpeg", ".gif",
    ".svg", ".ico", ".woff", ".woff2",
    ".min.js", ".min.css",
}

SKIP_FILENAMES = {
    "package-lock.json", "yarn.lock", "poetry.lock",
    "Pipfile.lock", "composer.lock", ".env.example", "CHANGELOG.md",
}

MAX_LINES_PER_FILE = 200


@dataclass
class FileDiff:
    file_path: str
    language: str
    changed_lines: list[tuple[int, str]]
    raw_diff: str


def should_skip_file(file_path: str) -> bool:
    filename = file_path.split("/")[-1]
    if filename in SKIP_FILENAMES:
        return True
    for ext in SKIP_EXTENSIONS:
        if file_path.endswith(ext):
            return True
    return False


def detect_language(file_path: str) -> str:
    ext_map = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript",
        ".jsx": "React/JSX", ".tsx": "React/TSX", ".java": "Java",
        ".go": "Go", ".rs": "Rust", ".rb": "Ruby", ".php": "PHP",
        ".cs": "C#", ".cpp": "C++", ".c": "C", ".sh": "Shell",
        ".yml": "YAML", ".yaml": "YAML", ".tf": "Terraform", ".sql": "SQL",
    }
    for ext, lang in ext_map.items():
        if file_path.endswith(ext):
            return lang
    return "Unknown"


def parse_diff(raw_diff: str) -> list[FileDiff]:
    file_diffs = []
    current_file = None
    current_lines = []
    current_raw = []
    line_number = 0

    for line in raw_diff.splitlines():
        if line.startswith("diff --git"):
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
            current_file = line[6:]
            current_raw.append(line)
        elif line.startswith("@@ "):
            match = re.search(r"\+(\d+)", line)
            if match:
                line_number = int(match.group(1)) - 1
            current_raw.append(line)
        elif line.startswith("+") and not line.startswith("+++"):
            line_number += 1
            current_lines.append((line_number, line[1:]))
            current_raw.append(line)
        elif line.startswith("-") and not line.startswith("---"):
            current_raw.append(line)
        else:
            line_number += 1
            current_raw.append(line)

    if current_file and current_lines:
        file_diffs.append(FileDiff(
            file_path=current_file,
            language=detect_language(current_file),
            changed_lines=current_lines[:MAX_LINES_PER_FILE],
            raw_diff="\n".join(current_raw),
        ))

    return [f for f in file_diffs if not should_skip_file(f.file_path)]
