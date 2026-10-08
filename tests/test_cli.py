"""The command line: exit codes, output files, and the missing-directory case."""

import contextlib
import io
import json
import os
import subprocess
import sys
import unittest

from reportgate.cli import main
from support import EXAMPLE_REPO, EXAMPLE_REPORTS, ROOT, TempDirTestCase


def run_cli(*args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main([str(a) for a in args])
    return code, out.getvalue(), err.getvalue()


class ExitCodes(TempDirTestCase):
    def test_missing_directory_exits_2(self):
        code, out, err = run_cli(self.tmp / "does-not-exist")
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("not found", err)

    def test_empty_directory_exits_2(self):
        empty = self.tmp / "empty"
        empty.mkdir()
        code, _out, err = run_cli(empty)
        self.assertEqual(code, 2)
        self.assertIn("no reports", err)

    def test_directory_with_only_unsupported_files_exits_2(self):
        reports = self.reports({"notes.pdf": "x", ".hidden.md": "# hidden"})
        code, _out, err = run_cli(reports)
        self.assertEqual(code, 2)
        self.assertIn("notes.pdf", err)

    def test_file_instead_of_directory_exits_2(self):
        reports = self.reports({"a.md": "# a"})
        self.assertEqual(run_cli(reports / "a.md")[0], 2)

    def test_missing_checkout_exits_2(self):
        code, _out, err = run_cli(EXAMPLE_REPORTS, "--repo", self.tmp / "nope")
        self.assertEqual(code, 2)
        self.assertIn("checkout", err)

    def test_success_exits_0(self):
        code, out, _err = run_cli(EXAMPLE_REPORTS, "--repo", EXAMPLE_REPO)
        self.assertEqual(code, 0)
        self.assertIn("This is triage, not confirmation.", out)

    def test_real_process_exit_codes(self):
        missing = subprocess.run(
            [sys.executable, "-m", "reportgate", str(self.tmp / "missing")],
            cwd=ROOT,
            capture_output=True,
        )
        self.assertEqual(missing.returncode, 2)
        ok = subprocess.run(
            [sys.executable, "-m", "reportgate", "examples/reports", "--repo", "examples/pastebox"],
            cwd=ROOT,
            capture_output=True,
        )
        self.assertEqual(ok.returncode, 0)
        self.assertIn("worth human review", ok.stdout.decode("utf-8"))

    def test_closed_pipe_is_not_an_error(self):
        # Output must be buffered, as it normally is, or the failure this guards against
        # (exit code 120 from a broken pipe found at shutdown) cannot happen.
        env = {k: v for k, v in os.environ.items() if k != "PYTHONUNBUFFERED"}
        long_output = ["examples/reports", "--repo", "examples/pastebox"]
        short_output = long_output + ["--out", str(self.tmp / "out")]
        for args in (long_output, short_output, ["--version"]):
            with self.subTest(args=args):
                process = subprocess.Popen(
                    [sys.executable, "-m", "reportgate", *args],
                    cwd=ROOT,
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                process.stdout.close()  # like `reportgate ... | head -1`
                _out, err = process.communicate()
                self.assertEqual(process.returncode, 0, err.decode("utf-8", "replace"))
                self.assertNotIn(b"Traceback", err)
                self.assertNotIn(b"Exception ignored", err)


class Outputs(TempDirTestCase):
    def test_out_writes_markdown_and_json(self):
        out_dir = self.tmp / "out"
        code, out, _err = run_cli(EXAMPLE_REPORTS, "--repo", EXAMPLE_REPO, "--out", out_dir)
        self.assertEqual(code, 0)
        self.assertIn("6 reports", out)
        markdown = (out_dir / "reportgate.md").read_text(encoding="utf-8")
        data = json.loads((out_dir / "reportgate.json").read_text(encoding="utf-8"))
        self.assertIn("# reportgate triage", markdown)
        self.assertEqual(data["summary"]["total"], 6)

    def test_json_flag_prints_json(self):
        code, out, _err = run_cli(EXAMPLE_REPORTS, "--json")
        self.assertEqual(code, 0)
        data = json.loads(out)
        self.assertFalse(data["tree"]["checked"])
        self.assertIsNone(data["tree"]["path"])

    def test_without_repo_says_tree_was_not_checked(self):
        code, out, _err = run_cli(EXAMPLE_REPORTS)
        self.assertEqual(code, 0)
        self.assertIn("Tree: **not checked**", out)
        code, out, _err = run_cli(EXAMPLE_REPORTS, "--out", self.tmp / "o")
        self.assertIn("The tree was not checked", out)

    def test_project_and_signature_options(self):
        code, out, _err = run_cli(
            EXAMPLE_REPORTS, "--repo", EXAMPLE_REPO, "--project", "Acme", "--signature", "Ada"
        )
        self.assertEqual(code, 0)
        self.assertIn("to Acme.", out)
        self.assertIn("— Ada", out)
        self.assertIn("—— Ada", out)

    def test_skipped_files_are_reported(self):
        reports = self.reports({"a.md": "# t\n\nbody", "b.json": "{not json", "c.pdf": "x"})
        code, out, err = run_cli(reports)
        self.assertEqual(code, 0)
        self.assertIn("skipped b.json", err)
        self.assertIn("## Skipped files", out)


if __name__ == "__main__":
    unittest.main()
