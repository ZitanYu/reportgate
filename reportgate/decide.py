"""Turn evidence into one of the six verdicts. The first rule that applies wins.

1. **duplicate**: the report is in a cluster and is not its primary report.
2. **missing location**: no file path, or every path escapes the repository.
3. **not in the current tree** (checkout given): the named file does not exist and
   the quoted code is nowhere in the checkout; or the file exists, the line is past
   its end, and the quoted code is nowhere in the checkout.
4. **missing minimal reproduction**: reproduction score 0 or 1.
5. **needs human judgment**: the signals conflict (the file exists but the quote
   does not match it, the line is past the end of the file, the code seems to have
   moved) or the reproduction is incomplete (score 2).
6. **worth human review**: everything else, which means a location and a
   reproduction scoring 3.

Without a checkout, rule 3 and the conflict checks in rule 5 cannot run; every
result then carries the reason ``tree_not_checked``.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from .model import (
    DUPLICATE,
    MISSING_LOCATION,
    MISSING_REPRODUCTION,
    NEEDS_HUMAN_JUDGMENT,
    NOT_IN_TREE,
    WORTH_HUMAN_REVIEW,
    Cluster,
    Evidence,
    Reason,
    Report,
)

RULE_ZH = {
    "same file and same CWE": "同一文件且同一 CWE",
    "same file and similar text": "同一文件且文字相近",
    "same CWE and similar text": "同一 CWE 且文字相近",
    "near-identical text": "文字几乎相同",
}


def code(text: str) -> str:
    return "`%s`" % text


def code_list(items: List[str]) -> str:
    return ", ".join(code(i) for i in items)


def where_en(path: str, line: Optional[int]) -> str:
    return "%s (line %d)" % (code(path), line) if line else code(path)


def where_zh(path: str, line: Optional[int]) -> str:
    return "%s 第 %d 行" % (code(path), line) if line else code(path)


def _tree_not_checked(path: Optional[str]) -> Reason:
    if path:
        return Reason(
            "tree_not_checked",
            "The tree was not checked (no checkout given), so %s was not verified." % code(path),
            "没有检查代码树（未提供代码检出），因此未核实 %s。" % code(path),
        )
    return Reason(
        "tree_not_checked",
        "The tree was not checked (no checkout given).",
        "没有检查代码树（未提供代码检出）。",
    )


def _reproduction_reason(ev: Evidence) -> Reason:
    r = ev.reproduction
    if r.score == 0:
        return Reason(
            "no_reproduction",
            "Reproduction score 0/3: the report contains no reproduction.",
            "复现评分 0/3：报告中没有任何复现。",
        )
    if r.score == 1:
        return Reason(
            "reproduction_mention_only",
            "Reproduction score 1/3: a reproduction is only mentioned; there are no steps "
            "and no code block.",
            "复现评分 1/3：只是提到了复现，没有步骤，也没有代码块。",
        )
    if r.score == 2:
        if r.code_block:
            have_en, have_zh = "a code block", "代码块"
            miss_en, miss_zh = "no steps and no payload", "没有步骤，也没有载荷"
        else:
            have_en, have_zh = "steps", "步骤"
            miss_en, miss_zh = "no code block", "没有代码块"
        return Reason(
            "reproduction_incomplete",
            "Reproduction score 2/3: the report has %s but %s." % (have_en, miss_en),
            "复现评分 2/3：报告有%s，但%s。" % (have_zh, miss_zh),
        )
    return Reason(
        "reproduction_present",
        "Reproduction score 3/3: a code block plus steps or a payload.",
        "复现评分 3/3：有代码块，并有步骤或载荷。",
    )


def _location_verified(ev: Evidence) -> Reason:
    path = ev.path or ""
    parts_en = ["%s exists" % code(path)]
    parts_zh = ["%s 存在" % code(path)]
    if ev.line_in_range is True:
        parts_en.append("line %d is in range" % ev.line)
        parts_zh.append("第 %d 行在范围内" % ev.line)
    elif ev.line_in_range is False:
        parts_en.append(
            "line %d is past the end of the file (%d lines), so line numbers have drifted"
            % (ev.line, ev.file_lines or 0)
        )
        parts_zh.append(
            "第 %d 行超出文件末尾（共 %d 行），行号已有偏移" % (ev.line, ev.file_lines or 0)
        )
    if ev.snippet_match is True:
        parts_en.append("the quoted code matches")
        parts_zh.append("引用的代码一致")
    en = parts_en[0] if len(parts_en) == 1 else ", ".join(parts_en[:-1]) + ", and " + parts_en[-1]
    return Reason("location_verified", en + ".", "，".join(parts_zh) + "。")


def decide(
    report: Report, ev: Evidence, cluster: Optional[Cluster], tree_checked: bool
) -> Tuple[str, List[Reason]]:
    """Return ``(verdict, reasons)`` for one report."""
    if cluster is not None and cluster.primary != report.id:
        others = [m for m in cluster.members if m != report.id]
        rules = sorted({link.rule for link in cluster.links if report.id in link.between})
        rule_en = "; ".join(rules) or "linked through another member"
        rule_zh = "；".join(RULE_ZH.get(r, r) for r in rules) or "经由组内其他报告关联"
        return DUPLICATE, [
            Reason(
                "duplicate_of",
                "Clustered with %s (%s); %s is the primary report."
                % (code_list(others), rule_en, code(cluster.primary)),
                "与 %s 归为一组（%s）；主报告是 %s。"
                % (code_list(others), rule_zh, code(cluster.primary)),
            )
        ]

    usable = [c for c in ev.candidates if not c.escapes_repo]
    if not usable:
        if ev.candidates:
            paths = code_list([c.path for c in ev.candidates])
            return MISSING_LOCATION, [
                Reason(
                    "all_paths_escape",
                    "Every path in the report points outside the repository (%s); such paths "
                    "are rejected and never read." % paths,
                    "报告中的路径都指向仓库之外（%s）；这类路径会被拒绝，不会被读取。" % paths,
                )
            ]
        return MISSING_LOCATION, [
            Reason("no_path", "The report names no file path.", "报告没有给出任何文件路径。")
        ]

    path = ev.path or ""
    reasons: List[Reason] = []
    conflicts: List[Reason] = []
    found = code_list(ev.snippet_found_in)
    if tree_checked:
        if ev.path_exists is False:
            if ev.snippet_found_in:
                conflicts.append(
                    Reason(
                        "code_moved",
                        "%s no longer exists, but the quoted code appears in %s."
                        % (code(path), found),
                        "%s 已不存在，但引用的代码出现在 %s。" % (code(path), found),
                    )
                )
            else:
                reasons.append(
                    Reason(
                        "path_missing",
                        "%s does not exist in the checkout." % code(path),
                        "检出中不存在 %s。" % code(path),
                    )
                )
                if ev.snippet_quoted:
                    reasons.append(
                        Reason(
                            "snippet_not_found",
                            "The quoted code does not appear anywhere in the checkout.",
                            "引用的代码在检出中的任何位置都找不到。",
                        )
                    )
                return NOT_IN_TREE, reasons
        else:
            line_reason = None
            if ev.line_in_range is False:
                line_reason = Reason(
                    "line_out_of_range",
                    "%s has %d lines; the report refers to line %d."
                    % (code(path), ev.file_lines or 0, ev.line),
                    "%s 只有 %d 行，而报告指向第 %d 行。"
                    % (code(path), ev.file_lines or 0, ev.line),
                )
            if ev.snippet_match is False:
                if ev.snippet_found_in:
                    conflicts.append(
                        Reason(
                            "snippet_elsewhere",
                            "The quoted code was found in %s instead of %s." % (found, code(path)),
                            "引用的代码出现在 %s，而不是 %s。" % (found, code(path)),
                        )
                    )
                elif line_reason is not None:
                    return NOT_IN_TREE, [
                        line_reason,
                        Reason(
                            "snippet_not_found",
                            "The quoted code does not appear anywhere in the checkout.",
                            "引用的代码在检出中的任何位置都找不到。",
                        ),
                    ]
                else:
                    conflicts.append(
                        Reason(
                            "snippet_mismatch",
                            "%s exists, but the quoted code does not match it." % code(path),
                            "%s 存在，但引用的代码与它不一致。" % code(path),
                        )
                    )
            if line_reason is not None and ev.snippet_match is not True:
                conflicts.append(line_reason)

    repro = ev.reproduction
    if repro.score <= 1:
        reasons.append(_reproduction_reason(ev))
        reasons.extend(conflicts)
        if not tree_checked:
            reasons.append(_tree_not_checked(path))
        return MISSING_REPRODUCTION, reasons
    if repro.score == 2:
        conflicts.append(_reproduction_reason(ev))
    if conflicts:
        if not tree_checked:
            conflicts.append(_tree_not_checked(path))
        return NEEDS_HUMAN_JUDGMENT, conflicts
    reasons.append(_location_verified(ev) if tree_checked else _tree_not_checked(path))
    reasons.append(_reproduction_reason(ev))
    return WORTH_HUMAN_REVIEW, reasons
