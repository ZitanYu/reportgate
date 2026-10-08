"""The verdicts, on the shipped examples and on small synthetic reports."""

import unittest

import reportgate
from reportgate import VERDICTS
from support import EXAMPLE_REPO, EXAMPLE_REPORTS, TempDirTestCase

APP = "def handle(name):\n    path = '/srv/' + name\n    return open(path).read()\n"

FULL_REPRO = """# Path traversal in handle()

`app/handler.py:2` builds a path from the request parameter `name`.

```python
path = '/srv/' + name
```

1. Start the app.
2. Call handle() with the value below.
3. A file outside /srv is returned.

```python
handle("../etc/hostname")
```
"""


class ExampleOutcomes(unittest.TestCase):
    """The examples in the README produce every verdict, one each."""

    @classmethod
    def setUpClass(cls):
        run = reportgate.triage(EXAMPLE_REPORTS, repo=EXAMPLE_REPO)
        cls.by_id = {r.report.id: r for r in run.results}
        cls.triage_run = run

    def verdict(self, report_id):
        return self.by_id[report_id].verdict

    def test_worth_human_review(self):
        result = self.by_id["01-upload-path-traversal.md"]
        self.assertEqual(result.verdict, "worth human review")
        ev = result.evidence
        self.assertEqual(ev.path, "pastebox/storage.py")
        self.assertTrue(ev.path_exists)
        self.assertEqual(ev.line, 16)
        self.assertTrue(ev.line_in_range)
        self.assertTrue(ev.snippet_match)
        self.assertEqual(ev.reproduction.score, 3)
        self.assertEqual(result.clustered_with, ["02-crafted-filename-write.json"])

    def test_duplicate(self):
        result = self.by_id["02-crafted-filename-write.json"]
        self.assertEqual(result.verdict, "duplicate")
        self.assertEqual(result.duplicate_of, "01-upload-path-traversal.md")

    def test_not_in_current_tree(self):
        result = self.by_id["03-title-html-injection.md"]
        self.assertEqual(result.verdict, "not in the current tree")
        self.assertEqual(result.evidence.path, "pastebox/templates.py")
        self.assertIs(result.evidence.path_exists, False)
        self.assertEqual(result.evidence.snippet_found_in, [])

    def test_missing_minimal_reproduction(self):
        result = self.by_id["04-large-paste.txt"]
        self.assertEqual(result.verdict, "missing minimal reproduction")
        self.assertTrue(result.evidence.path_exists)
        self.assertLessEqual(result.evidence.reproduction.score, 1)

    def test_missing_location(self):
        self.assertEqual(self.verdict("05-urgent-no-details.md"), "missing location")

    def test_needs_human_judgment(self):
        result = self.by_id["06-link-regex-backtracking.json"]
        self.assertEqual(result.verdict, "needs human judgment")
        self.assertTrue(result.evidence.line_in_range)
        self.assertIs(result.evidence.snippet_match, False)

    def test_every_verdict_is_one_of_the_six(self):
        for result in self.triage_run.results:
            self.assertIn(result.verdict, VERDICTS)
        self.assertEqual(set(self.triage_run.by_verdict().values()), {1})


class SyntheticOutcomes(TempDirTestCase):
    """Each core outcome from the smallest report that should produce it."""

    def triage(self, reports, repo_files=None):
        repo = self.repo(repo_files if repo_files is not None else {"app/handler.py": APP})
        return reportgate.triage(self.reports(reports), repo=repo)

    def test_worth_human_review(self):
        run = self.triage({"a.md": FULL_REPRO})
        self.assertEqual(run.results[0].verdict, "worth human review")

    def test_duplicate(self):
        second = FULL_REPRO.replace("# Path traversal in handle()", "# Reading arbitrary files")
        run = self.triage({"a.md": FULL_REPRO, "b.md": second})
        verdicts = [r.verdict for r in run.results]
        self.assertEqual(verdicts, ["worth human review", "duplicate"])

    def test_not_in_current_tree(self):
        report = FULL_REPRO.replace("app/handler.py", "app/old_handler.py").replace(
            "path = '/srv/' + name", "full = BASE + user_value"
        )
        run = self.triage({"a.md": report})
        self.assertEqual(run.results[0].verdict, "not in the current tree")

    def test_not_in_current_tree_when_line_and_quote_are_gone(self):
        report = FULL_REPRO.replace("app/handler.py:2", "app/handler.py:80").replace(
            "path = '/srv/' + name", "full = BASE + user_value"
        )
        run = self.triage({"a.md": report})
        result = run.results[0]
        self.assertEqual(result.verdict, "not in the current tree")
        self.assertIs(result.evidence.line_in_range, False)

    def test_missing_minimal_reproduction(self):
        run = self.triage({"a.txt": "Unsafe path\n\napp/handler.py looks unsafe to me.\n"})
        self.assertEqual(run.results[0].verdict, "missing minimal reproduction")

    def test_missing_location(self):
        run = self.triage({"a.txt": "RCE\n\nYour product has remote code execution.\n"})
        self.assertEqual(run.results[0].verdict, "missing location")

    def test_needs_human_judgment_for_incomplete_reproduction(self):
        report = "Bad path\n\nIn app/handler.py:\n\n1. Call handle with dots.\n2. See the file.\n"
        run = self.triage({"a.md": report})
        result = run.results[0]
        self.assertEqual(result.evidence.reproduction.score, 2)
        self.assertEqual(result.verdict, "needs human judgment")

    def test_moved_code_needs_human_judgment(self):
        report = FULL_REPRO.replace("app/handler.py", "app/legacy.py")
        run = self.triage({"a.md": report})
        result = run.results[0]
        self.assertEqual(result.verdict, "needs human judgment")
        self.assertEqual(result.evidence.snippet_found_in, ["app/handler.py"])

    def test_without_checkout_the_tree_is_not_checked(self):
        run = reportgate.triage(self.reports({"a.md": FULL_REPRO}))
        self.assertFalse(run.tree_checked)
        result = run.results[0]
        self.assertIsNone(result.evidence.path_exists)
        self.assertIn("tree_not_checked", [r.code for r in result.reasons])
        self.assertIn("not checked", reportgate.render_markdown(run))


if __name__ == "__main__":
    unittest.main()
