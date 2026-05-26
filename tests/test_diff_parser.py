import pytest
from reviewer.diff_parser import parse_diff, should_skip_file, detect_language

# Sample unified diff for testing
SAMPLE_DIFF = """diff --git a/reviewer/bot.py b/reviewer/bot.py
index abc1234..def5678 100644
--- a/reviewer/bot.py
+++ b/reviewer/bot.py
@@ -1,5 +1,10 @@
 import os
+import sys
+
+def dangerous_function():
+    password = "hardcoded_secret_123"
+    eval(user_input)
+    return password
 
 def main():
     pass
"""


def test_parse_diff_extracts_files():
    diffs = parse_diff(SAMPLE_DIFF)
    assert len(diffs) == 1
    assert diffs[0].file_path == "reviewer/bot.py"


def test_parse_diff_detects_language():
    diffs = parse_diff(SAMPLE_DIFF)
    assert diffs[0].language == "Python"


def test_parse_diff_only_added_lines():
    diffs = parse_diff(SAMPLE_DIFF)
    # Should only contain + lines, not - lines
    for line_num, content in diffs[0].changed_lines:
        assert not content.startswith("-")


def test_should_skip_lock_files():
    assert should_skip_file("package-lock.json") is True
    assert should_skip_file("poetry.lock") is True
    assert should_skip_file("yarn.lock") is True


def test_should_skip_by_extension():
    assert should_skip_file("logo.png") is True
    assert should_skip_file("styles.min.css") is True


def test_should_not_skip_source_files():
    assert should_skip_file("main.py") is False
    assert should_skip_file("index.ts") is False
    assert should_skip_file("App.jsx") is False


def test_detect_language():
    assert detect_language("main.py") == "Python"
    assert detect_language("index.ts") == "TypeScript"
    assert detect_language("main.go") == "Go"
    assert detect_language("unknown.xyz") == "Unknown"


def test_empty_diff():
    diffs = parse_diff("")
    assert diffs == []
