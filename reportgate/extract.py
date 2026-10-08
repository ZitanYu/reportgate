"""Pull locations, quoted code, and the stated entry point out of a report."""

from __future__ import annotations

import posixpath
import re
from typing import Dict, List, Optional

from .model import Candidate, Report
from .repro import PAYLOAD_RE, is_fix_block
from .text import CodeBlock, norm_line, remove_urls, sentences, split_code

# Extensions accepted for a bare file name with no directory part ("server.py").
# A path with a directory part ("docs/notes.txt") is accepted with any extension.
SOURCE_EXTENSIONS = frozenset(
    """
    py pyi pyx js jsx mjs cjs ts tsx vue svelte c h cc cpp cxx hh hpp hxx m mm go rs rb
    erb php java kt kts scala swift cs fs vb sh bash zsh ps1 pl pm lua sql r dart ex exs
    erl hrl hs clj cljs elm zig nim jl groovy gradle yml yaml toml ini cfg conf json xml
    html htm css scss sass less tf proto graphql gql cmake mk
    """.split()
)

_PATH_RE = re.compile(
    r"(?<![\w@$%&+=:/\\.~-])"
    r"(?P<path>"
    r"(?:[A-Za-z]:[\\/]|~[\\/]|\.{1,2}[\\/]|[\\/])?"
    r"(?:[\w.@+-]{1,255}[\\/]){0,64}"
    r"[\w@+-][\w.@+-]{0,254}\.[A-Za-z][A-Za-z0-9]{0,9}"
    r")"
    r"(?![\w\\/-])"
)

_LINE_AFTER = re.compile(
    r"""^(?:
        :(?P<colon>\d{1,7})
      | \#L(?P<anchor>\d{1,7})
      | [`'"*_)\]]{0,3}[ \t]{0,3}[(\[,]?[ \t]{0,3}(?:at[ \t]+|on[ \t]+)?
        (?:line|ln\.?|L)[ \t]{0,3}[:#]?[ \t]{0,3}(?P<word>\d{1,7})
      | [`'"*_)\]]{0,3}[ \t]{0,3}[(（]?[ \t]{0,3}第[ \t]{0,3}(?P<zh>\d{1,7})[ \t]{0,3}行
    )""",
    re.I | re.X,
)
_LINE_BEFORE = re.compile(
    r"(?:\bline|第)[ \t]{0,3}(?P<line>\d{1,7})[ \t]{0,3}行?[ \t]{0,3}(?:of|in|，|,)?[ \t]{0,3}[`'\"]?[ \t]{0,3}$",
    re.I,
)
_DECLARED = re.compile(
    r"^(?P<path>.*?)(?::(?P<colon>\d{1,7})(?:[-:]\d+)?|#L(?P<anchor>\d{1,7})(?:-L?\d+)?)?$"
)

_POC_INFOS = frozenset(
    {"sh", "bash", "shell", "console", "zsh", "fish", "powershell", "ps1", "pwsh", "cmd"}
    | {"bat", "batch", "http", "poc", "exploit", "curl", "terminal", "shell-session"}
)
_PROMPT_RE = re.compile(r"^[ \t]*(?:\$|>>>|%)[ \t]+\S|^[ \t]*[A-Za-z]:\\[^>\n]{0,200}>", re.M)
_COMMAND_RE = re.compile(
    r"^[ \t]*(?:curl|wget|nc|ncat|python3?[ \t]+-c|node[ \t]+-e|ruby[ \t]+-e|perl[ \t]+-e|php[ \t]+-r)\b",
    re.M | re.I,
)
_TRIVIAL_LINE = re.compile(r"^(?:\.{2,}|…+|[{}()\[\];,]+|(?://|#|--|/\*)\s*\.{2,}.*)$")

_ENTRY_STRONG = re.compile(
    r"\b(?:headers?|parameters?|params?|query\s+strings?|cookies?|form\s+fields?|argv"
    r"|command[\s-]line\s+(?:arguments?|options?|flags?)|environment\s+variables?|stdin"
    r"|multipart|endpoints?|request\s+(?:body|bodies|fields?|paths?|data))\b"
    r"|\b(?:an?|each|every|incoming|crafted|malicious|HTTP|POST|GET|PUT)\s+requests?\b"
    r"|请求头|请求体|请求参数|查询参数|命令行参数|环境变量|接口",
    re.I,
)
_ENTRY_WEAK = re.compile(
    r"\b(?:user[\s-](?:supplied|controlled|provided)|attacker[\s-]controlled|untrusted"
    r"|input|filename|upload\w*|payload)\b|用户可控|用户输入|不可信|输入|上传|文件名",
    re.I,
)


def lexically_escapes(path: str) -> bool:
    """True if ``path`` is absolute or climbs above its starting directory."""
    p = path.replace("\\", "/")
    if p.startswith("/") or p.startswith("~") or re.match(r"^[A-Za-z]:", p):
        return True
    depth = 0
    for part in p.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            depth -= 1
            if depth < 0:
                return True
        else:
            depth += 1
    return False


def normalize_path(path: str) -> str:
    """Normalise separators and ``./`` segments; leave escaping paths recognisable."""
    p = path.strip().strip("`'\"").replace("\\", "/")
    if not p:
        return ""
    if lexically_escapes(p):
        return p
    p = posixpath.normpath(p)
    return "" if p == "." else p


def _line_from(match: "re.Match[str]") -> Optional[int]:
    for name in ("colon", "anchor", "word", "zh", "line"):
        value = match.groupdict().get(name)
        if value:
            number = int(value)
            return number if number > 0 else None
    return None


def extract_candidates(report: Report) -> List[Candidate]:
    """All file paths named by a report: declared ones first, then ones in its text.

    Paths are taken from prose and inline code only. Fenced code blocks are skipped
    because paths inside a proof of concept are payloads, not locations.
    """
    found: List[Candidate] = []
    index: Dict[str, Candidate] = {}

    def add(raw: str, line: Optional[int], origin: str) -> None:
        path = normalize_path(raw)
        if not path:
            return
        existing = index.get(path)
        if existing is not None:
            if existing.line is None and line is not None:
                existing.line = line
            return
        candidate = Candidate(path=path, line=line, origin=origin)
        index[path] = candidate
        found.append(candidate)

    for raw in report.files:
        match = _DECLARED.match(raw.strip())
        if match:
            add(match.group("path"), _line_from(match), "declared")

    text = "\n".join(t for t in (report.title, report.body, report.suggested_fix) if t)
    prose, _blocks = split_code(text)
    prose = remove_urls(prose)
    for match in _PATH_RE.finditer(prose):
        raw = match.group("path")
        unified = raw.replace("\\", "/")
        has_dir = "/" in unified.rstrip("/")
        extension = unified.rsplit(".", 1)[-1].lower()
        if not has_dir and extension not in SOURCE_EXTENSIONS:
            continue
        line = None
        after = _LINE_AFTER.match(prose[match.end() : match.end() + 48])
        if after:
            line = _line_from(after)
        else:
            before = _LINE_BEFORE.search(prose[max(0, match.start() - 40) : match.start()])
            if before:
                line = _line_from(before)
        add(raw, line, "text")
    return found


def classify_block(block: CodeBlock) -> str:
    """Return ``"fix"``, ``"poc"``, or ``"quote"`` for a fenced code block.

    A *quote* is a block that appears to copy code from the project; it is what the
    snippet check compares with the checkout.
    """
    if is_fix_block(block):
        return "fix"
    if block.info in _POC_INFOS:
        return "poc"
    code = block.code
    if _PROMPT_RE.search(code) or _COMMAND_RE.search(code) or PAYLOAD_RE.search(code):
        return "poc"
    return "quote"


def significant_lines(code: str) -> List[str]:
    """Lines of a quote worth comparing: whitespace-collapsed, six or more characters."""
    out: List[str] = []
    for raw in code.split("\n"):
        line = norm_line(raw)
        if len(line) >= 6 and not _TRIVIAL_LINE.match(line):
            out.append(line)
    return out


def quoted_snippets(report: Report) -> List[List[str]]:
    """The significant lines of every block in the report that looks like a quote."""
    _prose, blocks = split_code(report.title + "\n" + report.body)
    out: List[List[str]] = []
    for block in blocks:
        if classify_block(block) == "quote":
            lines = significant_lines(block.code)
            if lines:
                out.append(lines)
    return out


def snippet_in_text(lines: List[str], normalized_text: str, threshold: float = 0.6) -> bool:
    """True if at least ``threshold`` of the quote's lines occur in the file text."""
    if not lines:
        return False
    hits = sum(1 for line in lines if line in normalized_text)
    return hits / len(lines) >= threshold


def entry_point(report: Report) -> Optional[str]:
    """The first sentence in which the reporter says where untrusted input enters.

    Sentences naming a request, header, parameter, argument, and so on win over
    sentences that only say "input" or "filename". The result is the reporter's
    claim, quoted, and is never verified.
    """
    prose, _blocks = split_code(report.body)
    candidates = [s for s in sentences(prose) if not s.lower().startswith("proof of concept")]
    for pattern in (_ENTRY_STRONG, _ENTRY_WEAK):
        for sentence in candidates:
            if pattern.search(sentence):
                cleaned = sentence.replace("**", "").strip()
                return cleaned if len(cleaned) <= 240 else cleaned[:237].rstrip() + "..."
    return None
