"""Turn report files into :class:`~reportgate.model.Report` objects.

A *reader* is any function ``reader(text, report_id) -> list[Report]``. It gets
the file's contents decoded as UTF-8 and the report id (the file's path relative
to the reports directory, with forward slashes). Readers are chosen by file
extension, and the mapping is replaceable::

    from reportgate import DEFAULT_READERS, triage

    def read_eml(text, report_id):
        ...

    readers = {**DEFAULT_READERS, ".eml": read_eml}
    run = triage("reports/", repo=".", readers=readers)

A reader that raises ``ValueError`` makes that one file show up under
``skipped`` instead of stopping the run.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from types import MappingProxyType
from typing import Callable, Dict, List, Mapping, Optional, Tuple

from .errors import ReportDirError
from .model import Report

Reader = Callable[[str, str], List[Report]]

MAX_REPORT_BYTES = 2_000_000

_CWE_RE = re.compile(r"\bCWE[\s:_-]{0,2}(\d{1,5})\b", re.I)
_SEVERITY_RE = re.compile(
    r"\b(?:severity|cvss\s+severity|严重程度|危害等级)\s*\**\s*[:：=]?\s*\**\s*"
    r"(critical|high|medium|moderate|low|informational|info|严重|高危|中危|低危)\b",
    re.I,
)
_TITLE_MARKUP = re.compile(r"^\s*(?:#{1,6}\s+|\*\*|__)|(?:\*\*|__|\s#+)\s*$")
_FIX_HEADING = re.compile(
    r"^[ \t]*(?:#{1,6}[ \t]*)?(?:\*\*)?[ \t]*"
    r"(?:(?:suggested|proposed|recommended|possible)[ \t]+)?"
    r"(?:fix(?:es)?|remediation|mitigation|patch|solution|修复建议|修复方案|建议修复|缓解措施)"
    r"[ \t]*(?:\*\*)?[ \t]*(?:[:：][^\n]*)?$",
    re.I,
)
_MD_HEADING = re.compile(r"^[ \t]{0,3}#{1,6}[ \t]")
_LABEL_LINE = re.compile(r"^[A-Z][A-Za-z ]{2,30}:[ \t]*$")
_CODE_HINT = re.compile(r"[(){}\[\];=$<>|`]|^\s*(?:curl|wget|python|node|ruby|php|go|java)\b")


def normalize_cwe(value: object) -> List[str]:
    """Return CWE ids as ``["CWE-22", ...]`` from a string, number, or list."""
    if value is None or value == "":
        return []
    if isinstance(value, (list, tuple)):
        out: List[str] = []
        for item in value:
            for cwe in normalize_cwe(item):
                if cwe not in out:
                    out.append(cwe)
        return out
    if isinstance(value, bool):
        return []
    if isinstance(value, int):
        return ["CWE-%d" % value]
    text = str(value).strip()
    if text.isdigit():
        return ["CWE-%d" % int(text)]
    found: List[str] = []
    for number in _CWE_RE.findall(text):
        cwe = "CWE-%d" % int(number)
        if cwe not in found:
            found.append(cwe)
    return found


def cwe_from_text(text: str) -> List[str]:
    return normalize_cwe(text)


def severity_from_text(text: str) -> Optional[str]:
    match = _SEVERITY_RE.search(text)
    return match.group(1).lower() if match else None


def split_fix_section(text: str) -> Tuple[str, str]:
    """Separate a "Suggested fix" / "修复建议" section from the rest of the text.

    The section starts at a heading or label naming a fix and runs to the next
    Markdown heading or the next ``Label:`` line. Returns ``(rest, fix)``.
    """
    lines = text.split("\n")
    keep: List[str] = []
    fix: List[str] = []
    in_fix = False
    in_fence = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_fence = not in_fence
        if not in_fence and _FIX_HEADING.match(line):
            in_fix = True
            fix.append(line)
            continue
        if in_fix and not in_fence and (_MD_HEADING.match(line) or _LABEL_LINE.match(stripped)):
            in_fix = False
        (fix if in_fix else keep).append(line)
    return "\n".join(keep).strip("\n"), "\n".join(fix).strip("\n")


def _clean(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")


def _split_title(text: str) -> Tuple[str, str]:
    lines = text.split("\n")
    for index, line in enumerate(lines):
        if line.strip():
            title = _TITLE_MARKUP.sub("", line).strip()
            body = "\n".join(lines[:index] + lines[index + 1 :]).strip("\n")
            return title[:200], body
    return "", ""


def _read_prose(text: str, report_id: str, fmt: str) -> List[Report]:
    text = _clean(text)
    title, body = _split_title(text)
    body, fix = split_fix_section(body)
    whole = title + "\n" + body
    return [
        Report(
            id=report_id,
            title=title or report_id,
            body=body,
            format=fmt,
            severity=severity_from_text(whole),
            cwe=cwe_from_text(whole),
            files=[],
            suggested_fix=fix,
        )
    ]


def read_markdown(text: str, report_id: str) -> List[Report]:
    """Read a Markdown report. The first non-empty line is the title."""
    return _read_prose(text, report_id, "markdown")


def read_text(text: str, report_id: str) -> List[Report]:
    """Read a plain-text report. The first non-empty line is the title."""
    return _read_prose(text, report_id, "text")


def _as_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (list, tuple)):
        return "\n".join(_as_text(v) for v in value)
    return json.dumps(value, ensure_ascii=False, indent=2)


def _as_paths(value: object) -> List[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        out: List[str] = []
        for item in value:
            out.extend(_as_paths(item))
        return out
    if isinstance(value, dict):
        for key in ("path", "file", "filename", "name"):
            if key in value:
                return _as_paths(value[key])
        return []
    return [p.strip() for p in re.split(r"[,\n]", str(value)) if p.strip()]


def _poc_section(poc: str) -> str:
    """Render a JSON proof-of-concept field as part of the report body."""
    poc = _clean(poc).strip("\n")
    if not poc.strip():
        return ""
    if "```" in poc or "~~~" in poc:
        return "Proof of concept:\n\n" + poc
    if "\n" in poc.strip() or _CODE_HINT.search(poc):
        fence = "````" if "```" in poc else "```"
        return "Proof of concept:\n\n%spoc\n%s\n%s" % (fence, poc, fence)
    return "Proof of concept: " + poc.strip()


def read_json(text: str, report_id: str) -> List[Report]:
    """Read one JSON report object, or a JSON array of report objects.

    Recognised fields: title, body, description, severity, cwe, files,
    affected_files, poc, proof_of_concept, suggested_fix. Other fields are ignored.
    """
    try:
        data = json.loads(_clean(text))
    except json.JSONDecodeError as exc:
        raise ValueError("invalid JSON: %s" % exc) from exc
    if isinstance(data, dict):
        items, numbered = [data], False
    elif isinstance(data, list):
        items, numbered = data, True
    else:
        raise ValueError("expected a JSON object or an array of objects")
    reports: List[Report] = []
    for index, item in enumerate(items, 1):
        if not isinstance(item, dict):
            raise ValueError("item %d is not a JSON object" % index)
        rid = "%s#%d" % (report_id, index) if numbered else report_id
        parts = [_as_text(item.get("description")), _as_text(item.get("body"))]
        body = "\n\n".join(p.strip("\n") for p in parts if p.strip())
        body, fix_in_body = split_fix_section(_clean(body))
        poc_parts = [_as_text(item.get(k)) for k in ("poc", "proof_of_concept")]
        poc = _poc_section("\n".join(p for p in poc_parts if p.strip()))
        if poc:
            body = (body + "\n\n" + poc).strip("\n")
        fix = "\n\n".join(
            p for p in (_as_text(item.get("suggested_fix")).strip(), fix_in_body) if p
        )
        title = _as_text(item.get("title")).strip().split("\n")[0][:200]
        if not title:
            title = next((ln.strip() for ln in body.split("\n") if ln.strip()), rid)[:200]
        cwe = normalize_cwe(item.get("cwe")) or cwe_from_text(title + "\n" + body)
        severity = _as_text(item.get("severity")).strip().lower() or severity_from_text(body)
        files: List[str] = []
        for path in _as_paths(item.get("files")) + _as_paths(item.get("affected_files")):
            if path not in files:
                files.append(path)
        reports.append(
            Report(
                id=rid,
                title=title,
                body=body,
                format="json",
                severity=severity or None,
                cwe=cwe,
                files=files,
                suggested_fix=fix,
            )
        )
    return reports


DEFAULT_READERS: Mapping[str, Reader] = MappingProxyType(
    {
        ".md": read_markdown,
        ".markdown": read_markdown,
        ".txt": read_text,
        ".json": read_json,
    }
)


def read_reports(
    directory: "os.PathLike[str] | str", readers: Optional[Mapping[str, Reader]] = None
) -> Tuple[List[Report], List[Dict[str, str]]]:
    """Read every report file under ``directory`` (recursively, sorted by path).

    Returns ``(reports, skipped)``. Hidden files and directories are ignored.
    Raises :class:`ReportDirError` if the directory is missing, is not a
    directory, or yields no reports at all.
    """
    readers = DEFAULT_READERS if readers is None else readers
    root = Path(directory)
    if not root.exists():
        raise ReportDirError("reports directory not found: %s" % root.as_posix())
    if not root.is_dir():
        raise ReportDirError("not a directory: %s" % root.as_posix())

    files: List[Path] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        for name in filenames:
            if not name.startswith("."):
                files.append(Path(dirpath) / name)
    files.sort(key=lambda p: p.relative_to(root).as_posix())

    reports: List[Report] = []
    skipped: List[Dict[str, str]] = []
    for path in files:
        rel = path.relative_to(root).as_posix()
        reader = readers.get(path.suffix.lower())
        if reader is None:
            skipped.append({"source": rel, "reason": "unsupported file type"})
            continue
        try:
            size = path.stat().st_size
            if size > MAX_REPORT_BYTES:
                skipped.append({"source": rel, "reason": "larger than %d bytes" % MAX_REPORT_BYTES})
                continue
            text = path.read_bytes().decode("utf-8", errors="replace")
            reports.extend(reader(text, rel))
        except (ValueError, OSError) as exc:
            skipped.append({"source": rel, "reason": str(exc)})

    if not reports:
        supported = ", ".join(sorted(readers))
        detail = "no reports (%s) in %s" % (supported, root.as_posix())
        if skipped:
            detail += "; skipped: " + "; ".join(
                "%s (%s)" % (s["source"], s["reason"]) for s in skipped
            )
        raise ReportDirError(detail)
    return reports, skipped
