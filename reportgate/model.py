"""Data model shared by the command line and the library.

Everything here is plain data. The JSON form of these objects is documented in
docs/SCHEMA.md and is produced by :func:`reportgate.render.to_dict`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# The six verdicts. These strings are part of the stable output schema.
DUPLICATE = "duplicate"
NOT_IN_TREE = "not in the current tree"
MISSING_LOCATION = "missing location"
MISSING_REPRODUCTION = "missing minimal reproduction"
WORTH_HUMAN_REVIEW = "worth human review"
NEEDS_HUMAN_JUDGMENT = "needs human judgment"

VERDICTS: Tuple[str, ...] = (
    DUPLICATE,
    NOT_IN_TREE,
    MISSING_LOCATION,
    MISSING_REPRODUCTION,
    WORTH_HUMAN_REVIEW,
    NEEDS_HUMAN_JUDGMENT,
)

VERDICT_CODES = {
    DUPLICATE: "duplicate",
    NOT_IN_TREE: "not_in_current_tree",
    MISSING_LOCATION: "missing_location",
    MISSING_REPRODUCTION: "missing_minimal_reproduction",
    WORTH_HUMAN_REVIEW: "worth_human_review",
    NEEDS_HUMAN_JUDGMENT: "needs_human_judgment",
}

VERDICT_ZH = {
    DUPLICATE: "重复",
    NOT_IN_TREE: "不在当前代码树中",
    MISSING_LOCATION: "缺少位置",
    MISSING_REPRODUCTION: "缺少最小复现",
    WORTH_HUMAN_REVIEW: "值得人工审查",
    NEEDS_HUMAN_JUDGMENT: "需要人工判断",
}

# A patch note is written for these verdicts and no others.
PATCH_NOTE_VERDICTS: Tuple[str, ...] = (WORTH_HUMAN_REVIEW, NEEDS_HUMAN_JUDGMENT)

REPRODUCTION_LABELS = {
    0: "nothing",
    1: "only a mention",
    2: "steps or a code block, but incomplete",
    3: "a code block plus steps or a payload",
}

REPRODUCTION_LABELS_ZH = {
    0: "没有",
    1: "只是提及",
    2: "有步骤或代码块，但不完整",
    3: "有代码块，并有步骤或载荷",
}

NOTICE_EN = (
    "This is triage, not confirmation. reportgate compared the reports with each other "
    "and, when a checkout was given, with the code; it did not run, exploit, or confirm "
    "anything."
)
NOTICE_ZH = (
    "这是分诊，不是确认。reportgate 只是把报告相互比较，并在提供了代码检出时与代码对照；"
    "它没有运行、利用或确认任何内容。"
)


@dataclass
class Report:
    """One incoming report, already parsed from its file.

    ``body`` holds everything that describes the issue and its reproduction.
    ``suggested_fix`` is kept apart so that a fix written by the reporter is never
    mistaken for a reproduction or for a quote of the current code.
    """

    id: str
    title: str
    body: str
    format: str = "text"
    severity: Optional[str] = None
    cwe: List[str] = field(default_factory=list)
    files: List[str] = field(default_factory=list)
    suggested_fix: str = ""


@dataclass
class Candidate:
    """A file path found in a report."""

    path: str
    line: Optional[int] = None
    origin: str = "text"  # "declared" (a JSON files field) or "text"
    escapes_repo: bool = False
    exists: Optional[bool] = None  # None when the tree was not checked or the path escapes


@dataclass
class Reason:
    """One reason behind a verdict, with a stable machine code and both languages."""

    code: str
    en: str
    zh: str


@dataclass
class Reproduction:
    """The 0-3 reproduction score and the signals it was computed from."""

    score: int
    mention: bool
    steps: bool
    code_block: bool
    payload: bool

    @property
    def label(self) -> str:
        return REPRODUCTION_LABELS[self.score]

    @property
    def label_zh(self) -> str:
        return REPRODUCTION_LABELS_ZH[self.score]


@dataclass
class Evidence:
    """What reportgate observed about one report."""

    candidates: List[Candidate]
    path: Optional[str]
    path_exists: Optional[bool]
    path_escapes_repo: bool
    line: Optional[int]
    line_in_range: Optional[bool]
    file_lines: Optional[int]
    snippet_quoted: bool
    snippet_match: Optional[bool]
    snippet_found_in: List[str]
    reproduction: Reproduction
    entry_point: Optional[str]


@dataclass
class ClusterLink:
    """Why two reports were put in the same cluster."""

    between: Tuple[str, str]
    rule: str
    shared_files: List[str]
    shared_cwe: List[str]
    text_overlap: float


@dataclass
class Cluster:
    """A group of reports that describe the same issue."""

    id: str
    primary: str
    members: List[str]
    links: List[ClusterLink]


@dataclass
class Result:
    """The full outcome for one report."""

    report: Report
    evidence: Evidence
    verdict: str
    reasons: List[Reason]
    cluster: Optional[Cluster]
    reply_en: str
    reply_zh: str
    patch_note: Optional[str]
    patch_note_reason: Optional[str]

    @property
    def clustered_with(self) -> List[str]:
        if self.cluster is None:
            return []
        return [m for m in self.cluster.members if m != self.report.id]

    @property
    def duplicate_of(self) -> Optional[str]:
        if self.cluster is None or self.cluster.primary == self.report.id:
            return None
        return self.cluster.primary


@dataclass
class TriageRun:
    """The outcome of one run over a batch of reports."""

    results: List[Result]
    reports_dir: Optional[str]
    tree_path: Optional[str]
    tree_checked: bool
    skipped: List[dict] = field(default_factory=list)
    project: Optional[str] = None

    def by_verdict(self) -> dict:
        counts = {v: 0 for v in VERDICTS}
        for result in self.results:
            counts[result.verdict] += 1
        return counts
