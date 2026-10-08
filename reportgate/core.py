"""The triage pipeline. The command line is a thin wrapper around :func:`triage`."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence

from .cluster import cluster_reports
from .decide import decide
from .extract import entry_point, extract_candidates, quoted_snippets, snippet_in_text
from .model import Candidate, Evidence, Report, Result, TriageRun
from .readers import Reader, read_reports
from .replies import write_patch_note, write_replies
from .repro import score_reproduction
from .text import split_code
from .tree import Tree

MAX_SNIPPET_LOCATIONS = 5


def _choose_primary(candidates: List[Candidate], checked: bool) -> Optional[Candidate]:
    usable = [c for c in candidates if not c.escapes_repo]
    if not usable:
        return candidates[0] if candidates else None

    def rank(c: Candidate) -> tuple:
        missing = 1 if (checked and not c.exists) else 0
        return (missing, 0 if c.origin == "declared" else 1, 0 if c.line else 1)

    return sorted(usable, key=rank)[0]


def analyze(report: Report, tree: Tree) -> Evidence:
    """Collect the evidence for one report. Reads the checkout; never writes to it."""
    candidates = extract_candidates(report)
    for candidate in candidates:
        candidate.escapes_repo, candidate.exists = tree.locate(candidate.path)
    primary = _choose_primary(candidates, tree.checked)

    prose, blocks = split_code(report.title + "\n" + report.body)
    reproduction = score_reproduction(prose, blocks)
    quotes = quoted_snippets(report)

    line = primary.line if primary else None
    line_in_range: Optional[bool] = None
    file_lines: Optional[int] = None
    snippet_match: Optional[bool] = None
    found_in: List[str] = []

    if primary is not None and not primary.escapes_repo and tree.checked:
        if primary.exists:
            loaded = tree.text(primary.path)
            if loaded is not None:
                file_lines, text = loaded
                if line is not None:
                    line_in_range = 1 <= line <= file_lines
                if quotes:
                    snippet_match = any(snippet_in_text(q, text) for q in quotes)
        if quotes and snippet_match is not True:
            for rel, text in tree.search_index():
                if rel == primary.path:
                    continue
                if any(snippet_in_text(q, text) for q in quotes):
                    found_in.append(rel)
                    if len(found_in) >= MAX_SNIPPET_LOCATIONS:
                        break

    return Evidence(
        candidates=candidates,
        path=primary.path if primary else None,
        path_exists=primary.exists if primary else None,
        path_escapes_repo=bool(primary and primary.escapes_repo),
        line=line,
        line_in_range=line_in_range,
        file_lines=file_lines,
        snippet_quoted=bool(quotes),
        snippet_match=snippet_match,
        snippet_found_in=found_in,
        reproduction=reproduction,
        entry_point=entry_point(report),
    )


def _display(path: "os.PathLike[str] | str | None") -> Optional[str]:
    return None if path is None else Path(path).as_posix()


def triage_reports(
    reports: Sequence[Report],
    repo: "os.PathLike[str] | str | None" = None,
    *,
    project: Optional[str] = None,
    signature: Optional[str] = None,
    reports_dir: Optional[str] = None,
    skipped: Optional[List[Dict[str, str]]] = None,
) -> TriageRun:
    """Triage reports you already have in memory.

    ``repo`` is the local checkout to compare against; without it the tree is not
    checked and every result says so. ``project`` names the project in replies
    (default: the checkout's directory name). ``signature`` signs the replies
    (default: "The maintainers" / "维护者").

    Raises :class:`~reportgate.errors.CheckoutError` if ``repo`` is not a directory.
    """
    tree = Tree(repo)
    if project is None and repo is not None:
        project = Path(repo).resolve().name or None
    reports = list(reports)
    evidence = [analyze(r, tree) for r in reports]
    clusters = cluster_reports(reports, evidence)

    results: List[Result] = []
    for report, ev in zip(reports, evidence, strict=True):
        cluster = clusters.get(report.id)
        verdict, reasons = decide(report, ev, cluster, tree.checked)
        reply_en, reply_zh = write_replies(
            report, ev, verdict, reasons, tree.checked, project=project, signature=signature
        )
        note, no_note = write_patch_note(report, ev, verdict, reasons, cluster, tree.checked)
        results.append(
            Result(
                report=report,
                evidence=ev,
                verdict=verdict,
                reasons=reasons,
                cluster=cluster,
                reply_en=reply_en,
                reply_zh=reply_zh,
                patch_note=note,
                patch_note_reason=no_note,
            )
        )
    return TriageRun(
        results=results,
        reports_dir=reports_dir,
        tree_path=_display(repo),
        tree_checked=tree.checked,
        skipped=list(skipped or []),
        project=project,
    )


def triage(
    reports_dir: "os.PathLike[str] | str",
    repo: "os.PathLike[str] | str | None" = None,
    *,
    readers: Optional[Mapping[str, Reader]] = None,
    project: Optional[str] = None,
    signature: Optional[str] = None,
) -> TriageRun:
    """Read every report in ``reports_dir`` and triage it against ``repo``.

    This is exactly what the ``reportgate`` command runs. Raises
    :class:`~reportgate.errors.ReportDirError` if the directory is missing or holds
    no reports, and :class:`~reportgate.errors.CheckoutError` if ``repo`` is given
    but is not a directory.
    """
    reports, skipped = read_reports(reports_dir, readers)
    return triage_reports(
        reports,
        repo,
        project=project,
        signature=signature,
        reports_dir=_display(reports_dir),
        skipped=skipped,
    )
