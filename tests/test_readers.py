"""Markdown, plain-text, and JSON readers, and replaceable reader functions."""

import unittest

import reportgate
from reportgate import DEFAULT_READERS, Report, read_json, read_markdown, read_text
from support import TempDirTestCase


class Readers(unittest.TestCase):
    def test_markdown_title_and_fields(self):
        report = read_markdown("# Bug in parser\n\nSeverity: High\nCWE-787 in src/p.c\n", "a.md")[0]
        self.assertEqual(report.title, "Bug in parser")
        self.assertEqual(report.severity, "high")
        self.assertEqual(report.cwe, ["CWE-787"])
        self.assertEqual(report.format, "markdown")

    def test_plain_text_first_line_is_title(self):
        report = read_text("\n\nOverflow in reader\nmore text\n", "a.txt")[0]
        self.assertEqual(report.title, "Overflow in reader")
        self.assertEqual(report.body, "more text")

    def test_json_object(self):
        text = '{"title": "T", "body": "B", "cwe": 22, "files": ["a.py"], "severity": "Low"}'
        report = read_json(text, "a.json")[0]
        self.assertEqual((report.id, report.title, report.cwe), ("a.json", "T", ["CWE-22"]))
        self.assertEqual((report.files, report.severity), (["a.py"], "low"))

    def test_json_array_gets_numbered_ids(self):
        reports = read_json('[{"title": "one"}, {"title": "two"}]', "batch.json")
        self.assertEqual([r.id for r in reports], ["batch.json#1", "batch.json#2"])

    def test_json_poc_becomes_a_code_block(self):
        report = read_json('{"title": "t", "poc": "run(\\"x\\")"}', "a.json")[0]
        self.assertIn("```poc", report.body)

    def test_invalid_json_raises_value_error(self):
        with self.assertRaises(ValueError):
            read_json("{nope", "a.json")
        with self.assertRaises(ValueError):
            read_json('"just a string"', "a.json")


class ReplaceableReaders(TempDirTestCase):
    def test_custom_reader_for_a_new_extension(self):
        def read_ini(text, report_id):
            fields = dict(line.split("=", 1) for line in text.splitlines() if "=" in line)
            return [Report(id=report_id, title=fields["title"], body=fields.get("body", ""))]

        reports = self.reports({"a.ini": "title=From INI\nbody=nothing here\n"})
        run = reportgate.triage(reports, readers={**DEFAULT_READERS, ".ini": read_ini})
        self.assertEqual(run.results[0].report.title, "From INI")

    def test_default_readers_cannot_be_mutated(self):
        with self.assertRaises(TypeError):
            DEFAULT_READERS[".x"] = read_text  # type: ignore[index]

    def test_reports_are_read_recursively_in_sorted_order(self):
        reports = self.reports({"b.md": "# b", "sub/a.txt": "a", "a.md": "# a"})
        run = reportgate.triage(reports)
        self.assertEqual([r.report.id for r in run.results], ["a.md", "b.md", "sub/a.txt"])


if __name__ == "__main__":
    unittest.main()
