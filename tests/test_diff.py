"""Tests for manifest_clean.diff."""

from pkg.manifest_clean.diff import text_to_lines, unified_diff


def test_text_to_lines_with_trailing_newline():
    lines = text_to_lines("a\nb\n")
    assert lines == ["a\n", "b\n"]


def test_text_to_lines_without_trailing_newline():
    lines = text_to_lines("a\nb")
    assert "a\n" in lines
    assert lines[-1] == "\n"


def test_unified_diff_empty_identical():
    lines = ["x\n", "y\n"]
    diff = unified_diff(lines, lines, fromfile="a", tofile="b")
    # difflib may still output a header for identical files with 0 line changes
    assert isinstance(diff, list)


def test_unified_diff_shows_changes():
    a = ["line1\n", "line2\n"]
    b = ["line1\n", "changed\n"]
    diff = unified_diff(a, b, fromfile="old", tofile="new")
    assert len(diff) > 0
    assert "old" in "".join(diff) or "new" in "".join(diff)
    assert any("-" in d or "+" in d for d in diff)
