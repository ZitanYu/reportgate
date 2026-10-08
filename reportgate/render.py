"""Render a :class:`~reportgate.model.TriageRun` as JSON or Markdown.

The JSON shape is documented field by field in docs/SCHEMA.md. It carries
``schema_version``; within one schema version fields are only ever added.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from ._version import __version__
from .model import (
    NOTICE_EN,
    NOTICE_ZH,
    VERDICT_CODES,
    VERDICT_ZH,
    VERDICTS,
    Result,
    TriageRun,
)

SCHEMA_VERSION = 1


def _result_dict(result: Result) -> Dict[str, Any]:
    report, ev = result.report, result.evidence
    cluster = None
    if result.cluster is not None:
        cluster = {
            "id": result.cluster.id,
            "primary": result.cluster.primary,
            "members": list(result.cluster.members),
            "links": [
                {
                    "between": list(link.between),
                    "rule": link.rule,
                    "shared_files": list(link.shared_files),
                    "shared_cwe": list(link.shared_cwe),
                    "text_overlap": link.text_overlap,
                }
                for link in result.cluster.links
            ],
        }
    return {
        "id": report.id,
        "format": report.format,
        "title": report.title,
        "severity": report.severity,
        "cwe": list(report.cwe),
        "verdict": result.verdict,
        "verdict_code": VERDICT_CODES[result.verdict],
        "verdict_zh": VERDICT_ZH[result.verdict],
        "reasons": [{"code": r.code, "en": r.en, "zh": r.zh} for r in result.reasons],
        "evidence": {
            "path": ev.path,
            "path_exists": ev.path_exists,
            "path_escapes_repo": ev.path_escapes_repo,
            "line": ev.line,
            "line_in_range": ev.line_in_range,
            "file_lines": ev.file_lines,
            "snippet_quoted": ev.snippet_quoted,
            "snippet_match": ev.snippet_match,
            "snippet_found_in": list(ev.snippet_found_in),
            "reproduction_score": ev.reproduction.score,
            "reproduction_label": ev.reproduction.label,
            "reproduction_signals": {
                "mention": ev.reproduction.mention,
                "steps": ev.reproduction.steps,
                "code_block": ev.reproduction.code_block,
                "payload": ev.reproduction.payload,
            },
            "entry_point": ev.entry_point,
            "candidates": [
                {
                    "path": c.path,
                    "line": c.line,
                    "origin": c.origin,
                    "escapes_repo": c.escapes_repo,
                    "exists": c.exists,
                }
                for c in ev.candidates
            ],
            "clustered_with": result.clustered_with,
            "duplicate_of": result.duplicate_of,
            "cluster": cluster,
        },
        "reply": {"en": result.reply_en, "zh": result.reply_zh},
        "patch_note": result.patch_note,
        "patch_note_reason": result.patch_note_reason,
    }


def to_dict(run: TriageRun) -> Dict[str, Any]:
    """The documented, stable JSON structure as plain Python data."""
    counts = run.by_verdict()
    return {
        "schema_version": SCHEMA_VERSION,
        "tool": {"name": "reportgate", "version": __version__},
        "notice": {"en": NOTICE_EN, "zh": NOTICE_ZH},
        "reports_dir": run.reports_dir,
        "tree": {"checked": run.tree_checked, "path": run.tree_path},
        "summary": {
            "total": len(run.results),
            "by_verdict": {v: counts[v] for v in VERDICTS},
        },
        "results": [_result_dict(r) for r in run.results],
        "skipped": [dict(s) for s in run.skipped],
    }


def render_json(run: TriageRun) -> str:
    return json.dumps(to_dict(run), ensure_ascii=False, indent=2) + "\n"


# --- Markdown -----------------------------------------------------------------


def _fence(content: str, info: str = "text") -> str:
    longest = 0
    run = 0
    for ch in content:
        run = run + 1 if ch == "`" else 0
        longest = max(longest, run)
    fence = "`" * max(3, longest + 1)
    return "%s%s\n%s\n%s" % (fence, info, content, fence)


def _cell(text: str) -> str:
    return text.replace("\\", "\\\\").replace("|", "\\|").replace("\n", " ")


def _code(text: str) -> str:
    if "`" in text:
        return "`` %s ``" % text
    return "`%s`" % text


def _yes_no(value: Optional[bool], none: str = "not checked") -> str:
    if value is None:
        return none
    return "yes" if value else "no"


def _exists_text(result: Result, checked: bool) -> str:
    ev = result.evidence
    if ev.path is None:
        return "n/a"
    if ev.path_escapes_repo:
        return "rejected (escapes the repository)"
    return _yes_no(ev.path_exists, "not checked")


def _line_text(result: Result, checked: bool) -> str:
    ev = result.evidence
    if ev.line is None:
        return "none given"
    if ev.line_in_range is None:
        if ev.path_escapes_repo:
            return "%d (not checked: path rejected)" % ev.line
        if checked and ev.path_exists is False:
            return "%d (not checked: file does not exist)" % ev.line
        return "%d (not checked)" % ev.line
    if ev.line_in_range:
        return "%d (in range; file has %d lines)" % (ev.line, ev.file_lines)
    return "%d (out of range; file has %d lines)" % (ev.line, ev.file_lines)


def _snippet_text(result: Result, checked: bool) -> str:
    ev = result.evidence
    if not ev.snippet_quoted:
        return "none quoted"
    if not checked:
        return "quoted (not checked)"
    if ev.snippet_match is True:
        text = "matches"
    elif ev.snippet_match is False:
        text = "does not match"
    else:
        text = "not compared (file missing)"
    if ev.snippet_found_in:
        text += "; found in " + ", ".join(_code(p) for p in ev.snippet_found_in)
    elif ev.snippet_match is not True:
        text += "; not found elsewhere in the tree"
    return text


def _cluster_text(result: Result) -> str:
    if result.cluster is None:
        return "none"
    others = ", ".join(_code(m) for m in result.clustered_with)
    rules = sorted({link.rule for link in result.cluster.links})
    role = (
        "primary"
        if result.duplicate_of is None
        else "duplicate of %s" % _code(result.cluster.primary)
    )
    return "%s (%s, %s: %s)" % (others, result.cluster.id, role, "; ".join(rules))


def _table_short(result: Result, checked: bool) -> List[str]:
    ev = result.evidence
    if ev.path is None:
        path = "none"
    else:
        path = _code(ev.path + (":%d" % ev.line if ev.line else ""))
    exists = _exists_text(result, checked)
    if exists.startswith("rejected"):
        exists = "rejected"
    if ev.line is None:
        line = "n/a"
    elif ev.line_in_range is None:
        line = "not checked" if not checked else "n/a"
    else:
        line = _yes_no(ev.line_in_range)
    if not ev.snippet_quoted:
        snippet = "none quoted"
    elif not checked:
        snippet = "not checked"
    elif ev.snippet_match is None:
        snippet = "found elsewhere" if ev.snippet_found_in else "not found"
    else:
        snippet = "matches" if ev.snippet_match else "no match"
    clustered = ", ".join(_code(m) for m in result.clustered_with) or "none"
    return [
        _code(result.report.id),
        result.verdict,
        path,
        exists,
        line,
        snippet,
        "%d/3" % ev.reproduction.score,
        clustered,
    ]


def render_markdown(run: TriageRun) -> str:
    """A human-readable report with every reply in a copyable block."""
    checked = run.tree_checked
    out: List[str] = ["# reportgate triage", ""]
    out.append("> **%s**" % NOTICE_EN)
    out.append(">")
    out.append("> **%s**" % NOTICE_ZH)
    out.append("")
    out.append("- Reports: %s (%d)" % (_code(run.reports_dir or "(in memory)"), len(run.results)))
    if checked:
        out.append("- Tree: %s (checked)" % _code(run.tree_path or ""))
    else:
        out.append(
            "- Tree: **not checked**. No checkout was given, so paths, lines, and quoted "
            "code were not verified. Run again with `--repo PATH` to check them."
        )
    out.append("- reportgate %s, output schema %d" % (__version__, SCHEMA_VERSION))
    out.append("")
    out.append("## Summary")
    out.append("")
    out.append("| Verdict | Reports |")
    out.append("|---|---|")
    counts = run.by_verdict()
    for verdict in VERDICTS:
        out.append("| %s | %d |" % (verdict, counts[verdict]))
    out.append("")
    out.append(
        "| Report | Verdict | Path | Exists | Line in range | Snippet | Repro | Clustered with |"
    )
    out.append("|---|---|---|---|---|---|---|---|")
    for result in run.results:
        out.append("| " + " | ".join(_cell(c) for c in _table_short(result, checked)) + " |")
    out.append("")

    for number, result in enumerate(run.results, 1):
        report, ev = result.report, result.evidence
        out.append(
            "## %d. %s: %s（%s）"
            % (number, _code(report.id), result.verdict, VERDICT_ZH[result.verdict])
        )
        out.append("")
        meta = ["**Title:** %s" % report.title]
        if report.severity:
            meta.append("**Severity (as reported):** %s" % report.severity)
        if report.cwe:
            meta.append("**CWE:** %s" % ", ".join(report.cwe))
        out.append(" · ".join(meta))
        out.append("")
        out.append("| Evidence | |")
        out.append("|---|---|")
        out.append("| Extracted path | %s |" % (_cell(_code(ev.path)) if ev.path else "none"))
        out.append("| Exists | %s |" % _cell(_exists_text(result, checked)))
        out.append("| Line | %s |" % _cell(_line_text(result, checked)))
        out.append("| Quoted snippet | %s |" % _cell(_snippet_text(result, checked)))
        out.append(
            "| Reproduction score | %d/3: %s |" % (ev.reproduction.score, ev.reproduction.label)
        )
        out.append("| Clustered with | %s |" % _cell(_cluster_text(result)))
        out.append("")
        others = [c for c in ev.candidates if c.path != ev.path]
        if others:
            described = []
            for c in others:
                if c.escapes_repo:
                    state = "rejected: escapes the repository"
                elif c.exists is None:
                    state = "not checked"
                else:
                    state = "exists" if c.exists else "does not exist"
                described.append("%s (%s)" % (_code(c.path), state))
            out.append("Other paths in the report: %s" % ", ".join(described))
            out.append("")
        out.append("**Why**")
        out.append("")
        for reason in result.reasons:
            out.append("- %s" % reason.en)
        out.append("")
        out.append("**Reply (English)**")
        out.append("")
        out.append(_fence(result.reply_en))
        out.append("")
        out.append("**回复（中文）**")
        out.append("")
        out.append(_fence(result.reply_zh))
        out.append("")
        if result.patch_note is not None:
            out.append("**Patch note**")
            out.append("")
            out.append(_fence(result.patch_note))
        else:
            out.append("**Patch note:** %s" % result.patch_note_reason)
        out.append("")

    if run.skipped:
        out.append("## Skipped files")
        out.append("")
        for item in run.skipped:
            out.append("- %s: %s" % (_code(item["source"]), item["reason"]))
        out.append("")
    return "\n".join(out).rstrip("\n") + "\n"
