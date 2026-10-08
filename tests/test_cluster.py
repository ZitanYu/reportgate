"""Clustering on shared files, identical CWE, and text overlap."""

import unittest

import reportgate
from reportgate import Report
from reportgate.cluster import link_rule, same_file
from support import TempDirTestCase


def report(rid, title, body, files=(), cwe=()):
    return Report(id=rid, title=title, body=body, files=list(files), cwe=list(cwe))


class ClusterRules(unittest.TestCase):
    def test_same_file_and_same_cwe_cluster_even_with_different_titles(self):
        a = report(
            "a.json",
            "Directory traversal in uploads",
            "Filenames are joined without checks.",
            files=["src/store.c"],
            cwe=["CWE-22"],
        )
        b = report(
            "b.json",
            "Arbitrary write primitive",
            "An attacker controls where bytes land on disk.",
            files=["src/store.c"],
            cwe=["CWE-22"],
        )
        run = reportgate.triage_reports([a, b])
        first, second = run.results
        self.assertEqual(first.clustered_with, ["b.json"])
        self.assertEqual(second.clustered_with, ["a.json"])
        self.assertEqual(second.verdict, "duplicate")
        self.assertEqual(second.duplicate_of, "a.json")
        self.assertEqual(first.cluster.links[0].rule, "same file and same CWE")

    def test_same_cwe_in_different_files_does_not_cluster(self):
        a = report("a", "XSS in header", "Header text is echoed.", ["web/header.js"], ["CWE-79"])
        b = report("b", "XSS in footer", "Footer links break out.", ["web/footer.js"], ["CWE-79"])
        run = reportgate.triage_reports([a, b])
        self.assertEqual([r.clustered_with for r in run.results], [[], []])

    def test_same_file_with_different_cwe_and_text_does_not_cluster(self):
        a = report("a", "Overflow", "Length is not checked before copy.", ["src/io.c"], ["CWE-787"])
        b = report("b", "Leak", "Descriptor stays open after errors.", ["src/io.c"], ["CWE-775"])
        run = reportgate.triage_reports([a, b])
        self.assertEqual([r.clustered_with for r in run.results], [[], []])

    def test_near_identical_text_clusters_without_files(self):
        text = "The login form accepts unlimited password attempts without delay or lockout."
        a = report("a", "No rate limit on login", text)
        b = report("b", "Brute force possible on login", text + " Please fix.")
        run = reportgate.triage_reports([a, b])
        self.assertEqual(run.results[1].verdict, "duplicate")

    def test_bare_file_name_matches_longer_path(self):
        self.assertTrue(same_file("lib/parse.rb", "parse.rb"))
        self.assertFalse(same_file("lib/parse.rb", "arse.rb"))
        rule, files, cwes = link_rule(["parse.rb"], ["lib/parse.rb"], ["CWE-20"], ["CWE-20"], 0.0)
        self.assertEqual(rule, "same file and same CWE")
        self.assertEqual(files, ["lib/parse.rb"])

    def test_clusters_are_transitive(self):
        a = report("a", "One", "alpha", ["x/one.py"], ["CWE-1"])
        b = report("b", "Two", "beta", ["x/one.py", "x/two.py"], ["CWE-1", "CWE-2"])
        c = report("c", "Three", "gamma", ["x/two.py"], ["CWE-2"])
        run = reportgate.triage_reports([a, b, c])
        self.assertEqual(run.results[0].clustered_with, ["b", "c"])
        self.assertEqual({r.cluster.id for r in run.results}, {"C1"})


class PrimarySelection(TempDirTestCase):
    def test_primary_is_the_report_with_the_better_reproduction(self):
        repo = self.repo({"app/db.py": "def find(q):\n    return run('SELECT ' + q)\n"})
        weak = "SQL injection\n\nCWE-89 in app/db.py, I think.\n"
        strong = (
            "# Query built from input\n\nCWE-89. `app/db.py:2` concatenates the query.\n\n"
            '1. Call find().\n2. Pass the value below.\n\n```python\nfind("1 UNION SELECT 1")\n```\n'
        )
        run = reportgate.triage(self.reports({"a-weak.txt": weak, "b-strong.md": strong}), repo)
        by_id = {r.report.id: r for r in run.results}
        self.assertEqual(by_id["a-weak.txt"].verdict, "duplicate")
        self.assertEqual(by_id["a-weak.txt"].duplicate_of, "b-strong.md")
        self.assertEqual(by_id["b-strong.md"].verdict, "worth human review")


if __name__ == "__main__":
    unittest.main()
