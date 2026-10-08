"""Path extraction and paths that escape the repository."""

import os
import time
import unittest

import reportgate
from reportgate import Report
from reportgate.extract import extract_candidates, lexically_escapes
from support import TempDirTestCase, write_files

SECRET = "TOP-SECRET-CONTENT"


class LexicalEscape(unittest.TestCase):
    def test_escaping_paths(self):
        for path in [
            "../secret.py",
            "a/../../secret.py",
            "/etc/passwd",
            "~/.ssh/config",
            "C:\\Windows\\win.ini",
            "..\\..\\boot.ini",
        ]:
            with self.subTest(path=path):
                self.assertTrue(lexically_escapes(path))

    def test_paths_that_stay_inside(self):
        for path in ["src/app.py", "./src/app.py", "a/../src/app.py", "src/./x/../app.py"]:
            with self.subTest(path=path):
                self.assertFalse(lexically_escapes(path))


class EscapeIsRejected(TempDirTestCase):
    def setUp(self):
        super().setUp()
        write_files(self.tmp, {"secret.py": SECRET + "\n"})
        self.checkout = self.repo({"src/app.py": "print('hello')\n"})

    def triage(self, report):
        return reportgate.triage_reports([report], self.checkout)

    def test_declared_dot_dot_path_is_rejected(self):
        run = self.triage(Report(id="r", title="t", body="", files=["../secret.py"]))
        result = run.results[0]
        self.assertEqual(result.verdict, "missing location")
        self.assertEqual(result.reasons[0].code, "all_paths_escape")
        self.assertTrue(result.evidence.path_escapes_repo)
        self.assertIsNone(result.evidence.path_exists)
        self.assertIsNone(result.evidence.file_lines)

    def test_absolute_path_is_rejected(self):
        run = self.triage(Report(id="r", title="t", body="", files=["/etc/passwd"]))
        self.assertTrue(run.results[0].evidence.candidates[0].escapes_repo)
        self.assertEqual(run.results[0].verdict, "missing location")

    def test_path_in_text_is_rejected(self):
        run = self.triage(Report(id="r", title="t", body="The bug is in ../../secret.py line 1."))
        self.assertTrue(run.results[0].evidence.path_escapes_repo)

    def test_quoted_secret_is_never_matched_through_an_escaping_path(self):
        body = "In ../secret.py:\n\n```\n%s\n```\n" % SECRET
        run = self.triage(Report(id="r", title="t", body=body))
        ev = run.results[0].evidence
        self.assertTrue(ev.path_escapes_repo)
        self.assertIsNone(ev.snippet_match)
        self.assertEqual(ev.snippet_found_in, [])

    def test_symlink_out_of_the_checkout_is_rejected(self):
        link = self.checkout / "src" / "link.py"
        try:
            os.symlink(self.tmp / "secret.py", link)
        except (OSError, NotImplementedError):
            self.skipTest("symbolic links are not available here")
        body = "`src/link.py:1`\n\n```\n%s\n```\n" % SECRET
        run = self.triage(Report(id="r", title="t", body=body))
        ev = run.results[0].evidence
        self.assertTrue(ev.path_escapes_repo)
        self.assertIsNone(ev.snippet_match)
        self.assertEqual(ev.snippet_found_in, [])

    def test_valid_path_is_used_when_another_escapes(self):
        report = Report(id="r", title="t", body="", files=["../secret.py", "src/app.py"])
        ev = self.triage(report).results[0].evidence
        self.assertEqual(ev.path, "src/app.py")
        self.assertTrue(ev.path_exists)


class Extraction(unittest.TestCase):
    def paths(self, body, files=()):
        report = Report(id="r", title="t", body=body, files=list(files))
        return [(c.path, c.line) for c in extract_candidates(report)]

    def test_colon_line(self):
        self.assertEqual(self.paths("see `src/app.py:42`"), [("src/app.py", 42)])

    def test_parenthesised_line(self):
        self.assertEqual(self.paths("in src/app.py (line 7) the"), [("src/app.py", 7)])

    def test_line_before_path(self):
        self.assertEqual(self.paths("at line 9 of src/app.py"), [("src/app.py", 9)])

    def test_declared_file_with_line(self):
        self.assertEqual(self.paths("", files=["lib/x.go:3"]), [("lib/x.go", 3)])

    def test_dot_slash_is_normalised(self):
        self.assertEqual(self.paths("./src/app.py"), [("src/app.py", None)])

    def test_urls_are_not_paths(self):
        self.assertEqual(self.paths("see https://example.com/src/app.py for details"), [])

    def test_paths_in_code_blocks_are_payloads_not_locations(self):
        self.assertEqual(self.paths("```\nopen('src/evil.py')\n```"), [])

    def test_bare_names_need_a_source_extension(self):
        self.assertEqual(
            self.paths("server.py and example.com and e.g. this"), [("server.py", None)]
        )

    def test_hostile_input_is_fast(self):
        hostile = [
            "a" * 300_000,
            "a/" * 100_000,
            "../" * 100_000,
            "x." * 100_000,
            ("curl " * 50_000),
            "\n" * 200_000,
        ]
        for body in hostile:
            start = time.perf_counter()
            reportgate.triage_reports([Report(id="r", title="t", body=body)])
            self.assertLess(time.perf_counter() - start, 5.0)


if __name__ == "__main__":
    unittest.main()
