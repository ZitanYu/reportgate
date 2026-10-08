"""reportgate: local triage for incoming vulnerability reports.

Give it a directory of reports and a local checkout. For each report it returns a
verdict, the evidence behind it, a Chinese reply, an English reply, and a patch
note only when one should be written. It runs entirely on your machine, never uses
the network, and never confirms a vulnerability: this is triage, not confirmation.

    >>> import reportgate
    >>> run = reportgate.triage("examples/reports", repo="examples/pastebox")
    >>> run.results[0].verdict
    'worth human review'

The command line and this library run the same code. The JSON output is
documented in docs/SCHEMA.md.

Author and security maintainer: Zitan Yu.
"""

from ._version import __version__
from .core import analyze, triage, triage_reports
from .errors import CheckoutError, ReportDirError, ReportgateError
from .model import (
    DUPLICATE,
    MISSING_LOCATION,
    MISSING_REPRODUCTION,
    NEEDS_HUMAN_JUDGMENT,
    NOT_IN_TREE,
    PATCH_NOTE_VERDICTS,
    VERDICT_CODES,
    VERDICTS,
    WORTH_HUMAN_REVIEW,
    Candidate,
    Cluster,
    ClusterLink,
    Evidence,
    Reason,
    Report,
    Reproduction,
    Result,
    TriageRun,
)
from .readers import DEFAULT_READERS, Reader, read_json, read_markdown, read_reports, read_text
from .render import SCHEMA_VERSION, render_json, render_markdown, to_dict
from .tree import Tree

__all__ = [
    "__version__",
    "SCHEMA_VERSION",
    "triage",
    "triage_reports",
    "analyze",
    "render_json",
    "render_markdown",
    "to_dict",
    "read_reports",
    "read_markdown",
    "read_text",
    "read_json",
    "DEFAULT_READERS",
    "Reader",
    "Tree",
    "ReportgateError",
    "ReportDirError",
    "CheckoutError",
    "VERDICTS",
    "VERDICT_CODES",
    "PATCH_NOTE_VERDICTS",
    "DUPLICATE",
    "NOT_IN_TREE",
    "MISSING_LOCATION",
    "MISSING_REPRODUCTION",
    "WORTH_HUMAN_REVIEW",
    "NEEDS_HUMAN_JUDGMENT",
    "Report",
    "Candidate",
    "Reason",
    "Reproduction",
    "Evidence",
    "Cluster",
    "ClusterLink",
    "Result",
    "TriageRun",
]
