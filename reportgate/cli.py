"""The ``reportgate`` command.

Exit codes: 0 on success (whatever the verdicts are), 2 when the reports
directory is missing or holds no reports, or the checkout is not a directory.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import List, Optional

from ._version import __version__
from .core import triage
from .errors import ReportgateError
from .model import NOTICE_EN, VERDICTS
from .render import render_json, render_markdown

EXIT_OK = 0
EXIT_USAGE = 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="reportgate",
        description=(
            "Triage a directory of incoming vulnerability reports against a local checkout: "
            "find duplicates, reports that do not match the current code, and reports "
            "without a minimal reproduction, and write ready-to-send replies. "
            "This is triage, not confirmation."
        ),
        epilog="Exit codes: 0 success; 2 missing or empty reports directory, or bad --repo.",
    )
    parser.add_argument(
        "reports_dir", metavar="REPORTS_DIR", help="directory of .md, .txt, and .json reports"
    )
    parser.add_argument(
        "--repo",
        metavar="PATH",
        help="local checkout to compare against (without it, the tree is not checked)",
    )
    parser.add_argument(
        "--out",
        metavar="DIR",
        help="write reportgate.md and reportgate.json into DIR instead of printing",
    )
    parser.add_argument(
        "--json", action="store_true", help="print JSON instead of Markdown (ignored with --out)"
    )
    parser.add_argument(
        "--project",
        metavar="NAME",
        help="project name used in replies (default: the checkout's directory name)",
    )
    parser.add_argument(
        "--signature",
        metavar="TEXT",
        help='how replies are signed (default: "The maintainers" / "维护者")',
    )
    parser.add_argument("--version", action="version", version="reportgate " + __version__)
    return parser


def _utf8_stdout() -> None:
    for stream in (sys.stdout, sys.stderr):
        encoding = (getattr(stream, "encoding", None) or "").lower().replace("-", "")
        reconfigure = getattr(stream, "reconfigure", None)
        if encoding != "utf8" and reconfigure is not None:
            try:
                reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass


def main(argv: Optional[List[str]] = None) -> int:
    """Run the command. Returns the exit code."""
    try:
        try:
            code = _run(argv)
        except SystemExit as exc:  # argparse exits by itself for --help, --version, bad usage
            code = 0 if exc.code is None else exc.code
        # Flush here, inside the try: output can sit in the buffer until exit (Python 3.14
        # buffers up to 128 KiB), and a broken pipe found during shutdown exits with 120.
        sys.stdout.flush()
        return code
    except BrokenPipeError:
        # The output was piped into something that stopped reading, such as `head`.
        # The run itself succeeded; send the rest to /dev/null so exit stays quiet.
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, sys.stdout.fileno())
        return EXIT_OK


def _run(argv: Optional[List[str]]) -> int:
    _utf8_stdout()
    args = build_parser().parse_args(argv)
    try:
        run = triage(
            args.reports_dir,
            repo=args.repo,
            project=args.project,
            signature=args.signature,
        )
    except ReportgateError as exc:
        print("reportgate: %s" % exc, file=sys.stderr)
        return EXIT_USAGE

    for item in run.skipped:
        print("reportgate: skipped %s (%s)" % (item["source"], item["reason"]), file=sys.stderr)

    if args.out:
        out_dir = Path(args.out)
        out_dir.mkdir(parents=True, exist_ok=True)
        md_path = out_dir / "reportgate.md"
        json_path = out_dir / "reportgate.json"
        md_path.write_text(render_markdown(run), encoding="utf-8", newline="\n")
        json_path.write_text(render_json(run), encoding="utf-8", newline="\n")
        counts = run.by_verdict()
        summary = ", ".join("%d %s" % (counts[v], v) for v in VERDICTS if counts[v])
        print("%d reports: %s." % (len(run.results), summary))
        if not run.tree_checked:
            print("The tree was not checked (no --repo given).")
        print("Wrote %s and %s" % (md_path.as_posix(), json_path.as_posix()))
        print(NOTICE_EN)
    elif args.json:
        sys.stdout.write(render_json(run))
    else:
        sys.stdout.write(render_markdown(run))
    return EXIT_OK


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
