"""Minimal Atlassian Document Format (ADF) builder.

Jira REST API v3 requires ADF (not plain strings) for rich-text fields such as comment bodies and
issue descriptions. Port of the proven Java ``Adf`` helper: blank lines separate paragraphs,
consecutive non-blank lines join with ``hardBreak`` nodes, and we never emit an empty-content
paragraph (which the v3 API can reject).
"""
from __future__ import annotations

from typing import Any


def from_plain_text(text: str) -> dict[str, Any]:
    """Wrap plain text into an ADF ``doc`` node."""
    content: list[dict[str, Any]] = []
    block: list[str] = []
    for line in (text or "").split("\n"):
        if line == "":
            _flush(content, block)
            block = []
        else:
            block.append(line)
    _flush(content, block)

    # Guarantee a valid, non-empty document even if the input was blank.
    if not content:
        content.append({"type": "paragraph", "content": [{"type": "text", "text": " "}]})
    return {"type": "doc", "version": 1, "content": content}


def _flush(content: list[dict[str, Any]], lines: list[str]) -> None:
    """Append one paragraph for the buffered lines (text nodes separated by hardBreaks)."""
    if not lines:
        return
    para_content: list[dict[str, Any]] = []
    for i, line in enumerate(lines):
        if i > 0:
            para_content.append({"type": "hardBreak"})
        para_content.append({"type": "text", "text": line})
    content.append({"type": "paragraph", "content": para_content})
