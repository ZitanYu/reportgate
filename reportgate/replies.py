"""Write the replies and the patch note for one result.

Replies are meant to be pasted as they are: no placeholders, no internal report
ids of other reporters, and an explicit statement that this is triage, not
confirmation. A patch note is written only for "worth human review" and "needs
human judgment"; every other verdict gets a one-line reason instead.
"""

from __future__ import annotations

from typing import List, Optional, Tuple

from .decide import code, code_list, where_en, where_zh
from .model import (
    DUPLICATE,
    MISSING_LOCATION,
    MISSING_REPRODUCTION,
    NEEDS_HUMAN_JUDGMENT,
    NOT_IN_TREE,
    PATCH_NOTE_VERDICTS,
    WORTH_HUMAN_REVIEW,
    Cluster,
    Evidence,
    Reason,
    Report,
)

DEFAULT_SIGNATURE_EN = "The maintainers"
DEFAULT_SIGNATURE_ZH = "维护者"

_TRIAGE_EN = "This is an initial triage, not a confirmation or a rejection of the issue."
_TRIAGE_ZH = "这只是初步分诊，既不是确认，也不是否定。"


def _open_en(report: Report, project: Optional[str]) -> str:
    to = " to %s" % project if project else ""
    return 'Hi,\n\nThank you for reporting "%s"%s.' % (report.title, to)


def _open_zh(report: Report, project: Optional[str]) -> str:
    if project:
        return "你好，\n\n感谢你向 %s 报告「%s」。" % (project, report.title)
    return "你好，\n\n感谢你报告「%s」。" % report.title


def _close_en(signature: Optional[str]) -> str:
    return "— %s" % (signature or DEFAULT_SIGNATURE_EN)


def _close_zh(signature: Optional[str]) -> str:
    return "—— %s" % (signature or DEFAULT_SIGNATURE_ZH)


def _bullet_en(reason: Reason) -> str:
    if reason.code == "reproduction_incomplete":
        return "The reproduction is incomplete: " + reason.en.split(": ", 1)[1]
    return reason.en


def _bullet_zh(reason: Reason) -> str:
    if reason.code == "reproduction_incomplete":
        return "复现不完整：" + reason.zh.split("：", 1)[1]
    return reason.zh


def _has(reasons: List[Reason], code_name: str) -> bool:
    return any(r.code == code_name for r in reasons)


def write_replies(
    report: Report,
    ev: Evidence,
    verdict: str,
    reasons: List[Reason],
    tree_checked: bool,
    project: Optional[str] = None,
    signature: Optional[str] = None,
) -> Tuple[str, str]:
    """Return ``(english, chinese)`` replies for one report."""
    path = ev.path or ""
    w_en, w_zh = where_en(path, ev.line), where_zh(path, ev.line)

    if verdict == DUPLICATE:
        en = [
            "This appears to describe the same issue as a report we have already received, "
            "so we will track the two together rather than separately. If you have details "
            "the other report may not cover, such as another entry point, another affected "
            "version, or a smaller reproduction, please reply with them and we will add them.",
            _TRIAGE_EN + " Please keep the details private for now.",
        ]
        zh = [
            "这份报告描述的问题似乎与我们已经收到的另一份报告相同，因此我们会把两者合并跟踪，"
            "而不是分开处理。如果你掌握对方可能没有提到的细节，例如其他入口、其他受影响的版本，"
            "或更小的复现，请回复告诉我们，我们会补充进去。",
            _TRIAGE_ZH + "目前请不要公开细节。",
        ]
    elif verdict == NOT_IN_TREE:
        if _has(reasons, "path_missing"):
            detail_en = "%s does not exist in the current tree" % code(path)
            detail_zh = "当前代码树中不存在 %s" % code(path)
            if ev.snippet_quoted:
                detail_en += ", and the code you quoted does not appear anywhere else"
                detail_zh += "，你引用的代码也没有出现在其他任何位置"
        else:
            detail_en = (
                "%s has only %d lines (the report refers to line %d), and the code you quoted "
                "does not appear in it or anywhere else in the tree"
                % (code(path), ev.file_lines or 0, ev.line or 0)
            )
            detail_zh = (
                "%s 只有 %d 行（报告指向第 %d 行），你引用的代码也不在该文件或代码树的其他位置"
                % (
                    code(path),
                    ev.file_lines or 0,
                    ev.line or 0,
                )
            )
        en = [
            "We compared the report with the current source tree and could not find what it "
            "describes: %s. The code may have changed, moved, or been fixed since the version "
            "you tested." % detail_en,
            "Could you tell us which version or commit you tested, and whether the issue still "
            "reproduces on the latest code? If it does, please point us to the current file "
            "and line.",
            _TRIAGE_EN,
        ]
        zh = [
            "我们把报告与当前源代码树做了对照，没有找到报告所描述的内容：%s。"
            "自你测试的版本以来，相关代码可能已被修改、移动或修复。" % detail_zh,
            "能否告诉我们你测试的是哪个版本或哪个提交，以及在最新代码上是否仍能复现？"
            "如果仍能复现，请告诉我们当前对应的文件和行号。",
            _TRIAGE_ZH,
        ]
    elif verdict == MISSING_LOCATION:
        if _has(reasons, "all_paths_escape"):
            paths = code_list([c.path for c in ev.candidates])
            lead_en = (
                "The paths in the report (%s) point outside the repository, so we cannot use "
                "them as a location in the code." % paths
            )
            lead_zh = "报告中的路径（%s）指向仓库之外，因此无法作为代码中的位置使用。" % paths
        else:
            lead_en = (
                "We could not find a file path in the report, so we cannot yet check it "
                "against the code."
            )
            lead_zh = "我们在报告中没有找到文件路径，因此暂时无法与代码对照。"
        en = [
            lead_en + " Could you reply with:",
            "- the file path, relative to the repository root, and the line number if you can;\n"
            "- where untrusted input enters, such as a request field, a file, or a "
            "command-line argument;\n"
            "- the version or commit you tested.",
            _TRIAGE_EN,
        ]
        zh = [
            lead_zh + "能否回复以下信息：",
            "- 文件路径（相对于仓库根目录），如有可能请附上行号；\n"
            "- 不可信输入从哪里进入，例如某个请求字段、某个文件或某个命令行参数；\n"
            "- 你测试的版本或提交。",
            _TRIAGE_ZH,
        ]
    elif verdict == MISSING_REPRODUCTION:
        if tree_checked:
            found_en = "We found the location the report refers to (%s)" % w_en
            found_zh = "我们找到了报告所指的位置（%s）" % w_zh
        else:
            found_en = "The report names %s" % w_en
            found_zh = "报告指出了 %s" % w_zh
        if ev.reproduction.score == 1:
            miss_en = "but the reproduction is only mentioned, not included"
            miss_zh = "但报告只是提到了复现，并没有附上"
        else:
            miss_en = "but the report does not include a minimal reproduction"
            miss_zh = "但报告没有附上最小复现"
        en = [
            "%s, %s. Before a maintainer can review it, could you reply with:"
            % (found_en, miss_en),
            "- the exact steps that trigger the behaviour;\n"
            "- the smallest input, request, or file that triggers it;\n"
            "- what you expected to happen and what happened instead;\n"
            "- the version or commit you tested.",
            _TRIAGE_EN,
        ]
        zh = [
            "%s，%s。在维护者审查之前，能否回复以下信息：" % (found_zh, miss_zh),
            "- 触发该行为的确切步骤；\n"
            "- 能触发它的最小输入、请求或文件；\n"
            "- 你预期的结果，以及实际发生的结果；\n"
            "- 你测试的版本或提交。",
            _TRIAGE_ZH,
        ]
    elif verdict == NEEDS_HUMAN_JUDGMENT:
        shown = [r for r in reasons if r.code != "tree_not_checked"]
        en = [
            "Our initial triage could not settle this report automatically:",
            "\n".join("- " + _bullet_en(r) for r in shown),
            "A maintainer will look at it by hand and may come back with questions. If you can "
            "tell us which version or commit you tested, that will help.",
            "This is triage, not confirmation: we have not confirmed whether the issue is "
            "exploitable. Please keep the details private while we review it.",
        ]
        zh = [
            "初步分诊无法自动得出结论：",
            "\n".join("- " + _bullet_zh(r) for r in shown),
            "维护者会人工查看，之后可能会向你提问。如果你能告诉我们测试的版本或提交，会很有帮助。",
            "这是分诊，不是确认：我们尚未确认该问题是否可被利用。审查期间请不要公开细节。",
        ]
    elif verdict == WORTH_HUMAN_REVIEW:
        if tree_checked:
            if ev.snippet_match:
                found_en = (
                    "The report points to %s, which exists in the current code. The code you "
                    "quoted matches that file, and the report includes a reproduction." % w_en
                )
            else:
                found_en = (
                    "The report points to %s, which exists in the current code, and it includes "
                    "a reproduction." % w_en
                )
            matched_zh = "，你引用的代码也与之一致" if ev.snippet_match else ""
            body_en = "We ran an initial triage. %s A maintainer will now review it by hand." % (
                found_en
            )
            body_zh = (
                "我们做了初步分诊：报告指向 %s，该位置在当前代码中存在%s，并且报告附带了复现。"
                "接下来会由维护者人工审查。" % (w_zh, matched_zh)
            )
        else:
            body_en = (
                "We ran an initial triage. The report points to %s and includes a reproduction. "
                "We have not yet compared it with the current code; a maintainer will review it "
                "by hand." % w_en
            )
            body_zh = (
                "我们做了初步分诊：报告指向 %s，并附带了复现。我们还没有把它与当前代码对照；"
                "接下来会由维护者人工审查。" % w_zh
            )
        en = [
            body_en,
            "This is triage, not confirmation: we have not confirmed whether the issue is "
            "exploitable. Please keep the details private until a fix is released; we will "
            "coordinate disclosure and credit with you.",
        ]
        zh = [
            body_zh,
            "这是分诊，不是确认：我们尚未确认该问题是否可被利用。在修复发布之前，请不要公开细节；"
            "披露时间和致谢方式我们会与你商定。",
        ]
    else:  # pragma: no cover - guarded by decide()
        raise ValueError("unknown verdict: %r" % verdict)

    english = "\n\n".join([_open_en(report, project)] + en + [_close_en(signature)])
    chinese = "\n\n".join([_open_zh(report, project)] + zh + [_close_zh(signature)])
    return english, chinese


def write_patch_note(
    report: Report,
    ev: Evidence,
    verdict: str,
    reasons: List[Reason],
    cluster: Optional[Cluster],
    tree_checked: bool,
) -> Tuple[Optional[str], Optional[str]]:
    """Return ``(patch_note, None)`` or ``(None, reason_no_note_was_written)``."""
    if verdict not in PATCH_NOTE_VERDICTS:
        if verdict == DUPLICATE and cluster is not None:
            why = (
                "No patch note: this report duplicates %s; any patch note belongs to that report."
                % cluster.primary
            )
        elif verdict == NOT_IN_TREE:
            why = (
                "No patch note: the reported code is not in the current tree, so there is "
                "nothing here to fix yet."
            )
        elif verdict == MISSING_LOCATION:
            why = "No patch note: the report gives no usable location in the repository."
        else:
            why = "No patch note: without a minimal reproduction there is no basis for a fix yet."
        return None, why

    path = ev.path or ""
    where = where_en(path, ev.line)
    if not tree_checked:
        where += " (not checked against the tree)"
    if ev.entry_point:
        entry = 'as described by the reporter, unverified: "%s"' % ev.entry_point
    else:
        entry = "not stated in the report; establish it before writing a fix."
    lines = [
        "Patch note (draft) for: %s" % report.title,
        "Report: %s" % report.id,
    ]
    if cluster is not None:
        others = [m for m in cluster.members if m != report.id]
        lines.append("Also covers duplicates: %s" % ", ".join(others))
    lines += [
        "",
        "- Exploitability: not confirmed. This note comes from triage; confirm the issue by "
        "hand before changing code.",
        "- Where untrusted input enters: %s" % entry,
        "- Path to fix: %s" % where,
    ]
    if report.cwe:
        lines.append("- Weakness: %s (as reported)" % ", ".join(report.cwe))
    if verdict == NEEDS_HUMAN_JUDGMENT:
        open_items = [r.en for r in reasons if r.code != "tree_not_checked"]
        lines.append("- Open questions: %s" % " ".join(open_items))
    lines.append(
        "- Release: publish the fix as a separate security release, not bundled with "
        "unrelated changes, and credit the reporter as agreed."
    )
    return "\n".join(lines), None
