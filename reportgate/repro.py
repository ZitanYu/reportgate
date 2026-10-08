"""Score how much of a reproduction a report contains, from 0 to 3.

=====  ==========================================================
score  meaning
=====  ==========================================================
0      nothing
1      only a mention ("I have a PoC", "can be exploited", ...)
2      steps or a code block, but incomplete
3      a code block plus steps or a payload
=====  ==========================================================

The score is computed from the report text only. A fenced block marked
``diff``/``patch`` (a proposed fix) is not counted as a code block, and the
reporter's suggested-fix section is never scored.

These patterns *detect* common payload shapes in text a reporter already wrote.
reportgate never generates, completes, or runs a payload.
"""

from __future__ import annotations

import re
from typing import List

from .model import Reproduction
from .text import CodeBlock

MENTION_RE = re.compile(
    r"\b(?:reproduc\w*|repro|poc|proof[\s-]of[\s-]concept|exploit\w*|trigger\w*|steps?\s+to)\b"
    r"|复现|重现|触发|利用|概念验证",
    re.I,
)

PAYLOAD_RE = re.compile(
    r"\.\./|\.\.\\|%2e%2e|<script|javascript:|\bonerror\s*=|\bonload\s*="
    r"|'\s*or\s+'?1'?\s*=\s*'?1|\bunion\s+(?:all\s+)?select\b|\$\{jndi:|\{\{\s*\d+\s*\*\s*\d+\s*\}\}"
    r"|<!ENTITY|file:///|169\.254\.169\.254|/etc/passwd|\\x[0-9a-fA-F]{2}|\bA{64,}"
    r"|\bcurl[ \t][^\n]{0,300}?[ \t]-(?:d|F|X|H|-data)\b"
    r"|^[ \t]*(?:GET|POST|PUT|DELETE|PATCH)[ \t]+/\S{0,2000}[ \t]+HTTP/\d",
    re.I | re.M,
)

_NUMBERED = re.compile(r"^\s{0,6}\d{1,3}[.)]\s+\S", re.M)
_BULLET = re.compile(r"^\s{0,6}[-*+]\s+\S", re.M)
_STEPS_HEADING = re.compile(
    r"steps?\s+to\s+reproduc\w*|reproduction\s+steps|\bsteps\b|how\s+to\s+reproduc\w*|复现步骤|重现步骤|步骤",
    re.I,
)
_FIX_INFOS = frozenset({"diff", "patch"})


def is_fix_block(block: CodeBlock) -> bool:
    """A block that proposes a change rather than reproducing the issue."""
    if block.info in _FIX_INFOS:
        return True
    lines = block.code.split("\n")
    if any(line.startswith("@@ ") for line in lines):
        return True
    return any(line.startswith("--- ") for line in lines) and any(
        line.startswith("+++ ") for line in lines
    )


def has_steps(prose: str) -> bool:
    """Two or more numbered items, or two or more bullets under a steps heading."""
    if len(_NUMBERED.findall(prose)) >= 2:
        return True
    match = _STEPS_HEADING.search(prose)
    if match:
        after = prose[match.end() :]
        return len(_BULLET.findall(after)) >= 2
    return False


def score_reproduction(prose: str, blocks: List[CodeBlock]) -> Reproduction:
    """Score the reproduction in ``prose`` (text outside code) and ``blocks``."""
    code_blocks = [b for b in blocks if b.code.strip() and not is_fix_block(b)]
    code = bool(code_blocks)
    steps = has_steps(prose)
    all_text = prose + "\n" + "\n".join(b.code for b in code_blocks)
    payload = bool(PAYLOAD_RE.search(all_text))
    mention = bool(MENTION_RE.search(prose))
    if code and (steps or payload):
        score = 3
    elif code or steps:
        score = 2
    elif mention or payload:
        score = 1
    else:
        score = 0
    return Reproduction(score=score, mention=mention, steps=steps, code_block=code, payload=payload)
