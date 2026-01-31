"""Unified diff and change detection."""

from __future__ import annotations

import difflib
from typing import Any


def unified_diff(
    a_lines: list[str],
    b_lines: list[str],
    fromfile: str = "a",
    tofile: str = "b",
    lineterm: str = "\n",
) -> list[str]:
    """Return unified diff lines between a_lines and b_lines."""
    return list(
        difflib.unified_diff(
            a_lines,
            b_lines,
            fromfile=fromfile,
            tofile=tofile,
            lineterm=lineterm,
        )
    )


def text_to_lines(text: str) -> list[str]:
    """Split text into lines, preserving final newline behavior for diff."""
    if not text.endswith("\n"):
        return text.splitlines(keepends=True) + ["\n"]
    return text.splitlines(keepends=True)


def lines_to_text(lines: list[str]) -> str:
    """Join lines back to a single string."""
    return "".join(lines)
