"""The JSON schema matches docs/SCHEMA.md, and shipped sample output is real."""

import json
import re
import unittest

import reportgate
from reportgate import VERDICTS
from support import EXAMPLE_REPO, EXAMPLE_REPORTS, ROOT, InRepoRoot, TempDirTestCase

SCHEMA_DOC = ROOT / "docs" / "SCHEMA.md"
EXPECTED = ROOT / "examples" / "expected"
LEAF_OBJECTS = {"summary.by_verdict"}


def documented_fields():
    fields = set()
    for line in SCHEMA_DOC.read_text(encoding="utf-8").splitlines():
        match = re.match(r"^\| `([a-z_\[\].]+)` \| (?!`)", line)
        if match:
            fields.add(match.group(1))
    return fields


def flatten(value, prefix=""):
    paths = set()
    if isinstance(value, dict):
        for key, child in value.items():
            path = prefix + "." + key if prefix else key
            paths.add(path)
            if path not in LEAF_OBJECTS:
                paths |= flatten(child, path)
    elif isinstance(value, list):
        for child in value:
            if isinstance(child, dict):
                paths |= flatten(child, prefix + "[]")
    return paths


class Schema(TempDirTestCase):
    def test_documented_fields_match_real_output(self):
        full = reportgate.to_dict(reportgate.triage(EXAMPLE_REPORTS, repo=EXAMPLE_REPO))
        reports = self.reports({"a.md": "# t\n\nbody", "bad.json": "{"})
        with_skip = reportgate.to_dict(reportgate.triage(reports))
        actual = flatten(full) | flatten(with_skip)
        documented = documented_fields()
        self.assertEqual(actual - documented, set(), "fields missing from docs/SCHEMA.md")
        self.assertEqual(documented - actual, set(), "documented fields never produced")

    def test_schema_version_and_verdicts(self):
        data = reportgate.to_dict(reportgate.triage(EXAMPLE_REPORTS, repo=EXAMPLE_REPO))
        self.assertEqual(data["schema_version"], 1)
        self.assertEqual(list(data["summary"]["by_verdict"]), list(VERDICTS))
        self.assertEqual(
            set(VERDICTS),
            {
                "duplicate",
                "not in the current tree",
                "missing location",
                "missing minimal reproduction",
                "worth human review",
                "needs human judgment",
            },
        )


class ShippedOutput(unittest.TestCase):
    """examples/expected and the README sample are real output, byte for byte."""

    @classmethod
    def setUpClass(cls):
        with InRepoRoot():
            run = reportgate.triage("examples/reports", repo="examples/pastebox")
        cls.markdown = reportgate.render_markdown(run)
        cls.json = reportgate.render_json(run)

    def read(self, path):
        return path.read_text(encoding="utf-8").replace("\r\n", "\n")

    def test_expected_markdown_is_current(self):
        self.assertEqual(self.read(EXPECTED / "reportgate.md"), self.markdown)

    def test_expected_json_is_current(self):
        self.assertEqual(json.loads(self.read(EXPECTED / "reportgate.json")), json.loads(self.json))

    def test_readme_sample_output_is_real(self):
        readme = self.read(ROOT / "README.md")
        blocks = re.findall(
            r"<!-- sample-output:start -->\n````text\n(.*?)\n````\n<!-- sample-output:end -->",
            readme,
            re.S,
        )
        self.assertTrue(blocks, "README has no sample output block")
        for block in blocks:
            for chunk in block.split("\n[...]\n"):
                self.assertIn(chunk, self.markdown)


if __name__ == "__main__":
    unittest.main()
