"""Helpers shared by the tests. Uses only the standard library."""

import os
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "examples"
EXAMPLE_REPORTS = EXAMPLES / "reports"
EXAMPLE_REPO = EXAMPLES / "pastebox"


def write_files(base, files):
    """Write ``{relative_path: text}`` under ``base`` and return ``base``."""
    base = Path(base)
    for rel, text in files.items():
        path = base / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return base


class TempDirTestCase(unittest.TestCase):
    """A test case with a fresh temporary directory in ``self.tmp``."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def reports(self, files):
        return write_files(self.tmp / "reports", files)

    def repo(self, files):
        return write_files(self.tmp / "repo", files)


class InRepoRoot:
    """Context manager: run with the repository root as the working directory."""

    def __enter__(self):
        self._old = os.getcwd()
        os.chdir(ROOT)
        return ROOT

    def __exit__(self, *exc):
        os.chdir(self._old)
        return False
