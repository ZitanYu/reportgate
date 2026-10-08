"""Small text helpers used by the readers and the rules.

All regular expressions here are written to run in linear time on hostile input:
reports come from strangers, and a triage tool must not hang on one of them.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Set, Tuple

_FENCE_OPEN = re.compile(r"^[ \t]{0,3}(`{3,}|~{3,})[ \t]*([^`\n]*)$")
URL_RE = re.compile(r"\b[A-Za-z][A-Za-z0-9+.-]{0,20}://\S+")
_WORD_RE = re.compile(r"[a-z0-9_]{3,40}")
_CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]+")
_SENTENCE_END = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9`\"'(\[*_])|(?<=[。！？；])")
_LINE_MARKER = re.compile(r"^\s*(?:#{1,6}\s+|[-*+]\s+|\d{1,3}[.)]\s+|>\s*)")

STOPWORDS = frozenset(
    """
    the and for that this with from are was were has have had can could would should will
    not but you your our its into when then than which there their been being also any all
    may might does did use used using via per such more most other some only just like
    very about after before because while where what who how why here over under out off
    file line code issue report reported vulnerability vulnerable security please thanks
    thank hello dear team found find see seen let lets get got make made one two three
    """.split()
)


@dataclass
class CodeBlock:
    """A fenced code block. ``info`` is the lower-cased first word after the fence."""

    info: str
    code: str


def split_code(text: str) -> Tuple[str, List[CodeBlock]]:
    """Split Markdown-ish text into prose and fenced code blocks.

    Code blocks are replaced by a blank line in the prose so that line structure
    (numbered steps, headings) is preserved. An unclosed fence runs to the end.
    """
    prose: List[str] = []
    blocks: List[CodeBlock] = []
    lines = text.split("\n")
    i = 0
    while i < len(lines):
        match = _FENCE_OPEN.match(lines[i])
        if not match:
            prose.append(lines[i])
            i += 1
            continue
        fence = match.group(1)
        info_words = match.group(2).strip().split()
        info = info_words[0].lower() if info_words else ""
        code_lines: List[str] = []
        i += 1
        while i < len(lines):
            stripped = lines[i].strip()
            if stripped and set(stripped) == {fence[0]} and len(stripped) >= len(fence):
                break
            code_lines.append(lines[i])
            i += 1
        blocks.append(CodeBlock(info=info, code="\n".join(code_lines)))
        prose.append("")
        i += 1
    return "\n".join(prose), blocks


def remove_urls(text: str) -> str:
    """Replace URLs with a space so their path parts are not read as file paths."""
    return URL_RE.sub(" ", text)


def sentences(prose: str) -> List[str]:
    """Split prose into sentences; paragraphs and list items always break."""
    out: List[str] = []
    for paragraph in re.split(r"\n\s*\n", prose):
        items: List[str] = []
        for raw in paragraph.split("\n"):
            if _LINE_MARKER.match(raw) or not items:
                items.append(_LINE_MARKER.sub("", raw).strip())
            else:
                items[-1] = (items[-1] + " " + raw.strip()).strip()
        for item in items:
            for sentence in _SENTENCE_END.split(item):
                sentence = sentence.strip()
                if sentence:
                    out.append(sentence)
    return out


def tokens(text: str) -> Set[str]:
    """Word tokens for text overlap: lower-case words plus CJK character bigrams."""
    lower = text.lower()
    out = {w for w in _WORD_RE.findall(lower) if w not in STOPWORDS and not w.isdigit()}
    for run in _CJK_RE.findall(text):
        if len(run) == 1:
            out.add(run)
        else:
            out.update(run[i : i + 2] for i in range(len(run) - 1))
    return out


def jaccard(a: Set[str], b: Set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def norm_line(line: str) -> str:
    """Collapse all whitespace in a line so quotes survive re-indentation."""
    return " ".join(line.split())
