"""Replies are ready to paste, and patch notes appear only when warranted."""

import re
import unittest

import reportgate
from reportgate import PATCH_NOTE_VERDICTS
from support import EXAMPLE_REPO, EXAMPLE_REPORTS

PLACEHOLDER = re.compile(r"\{[a-z_]*\}|%[sd]|TODO|TBD|XXX|<[A-Z_ ]+>|\[(?:NAME|PROJECT)\]")


class RepliesAndPatchNotes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.results = reportgate.triage(EXAMPLE_REPORTS, repo=EXAMPLE_REPO).results
        cls.unchecked = reportgate.triage(EXAMPLE_REPORTS).results

    def all_results(self):
        return list(self.results) + list(self.unchecked)

    def test_every_result_has_both_replies(self):
        for result in self.all_results():
            with self.subTest(report=result.report.id):
                self.assertTrue(result.reply_en.startswith("Hi,"))
                self.assertTrue(result.reply_zh.startswith("你好，"))
                self.assertIn(result.report.title, result.reply_en)
                self.assertIn(result.report.title, result.reply_zh)

    def test_replies_say_this_is_triage_not_confirmation(self):
        for result in self.all_results():
            with self.subTest(report=result.report.id):
                self.assertRegex(result.reply_en, r"triage, not (a )?confirmation")
                self.assertIn("分诊", result.reply_zh)

    def test_replies_have_no_placeholders(self):
        for result in self.all_results():
            for text in (result.reply_en, result.reply_zh, result.patch_note or ""):
                with self.subTest(report=result.report.id):
                    self.assertIsNone(PLACEHOLDER.search(text), text)

    def test_duplicate_reply_does_not_reveal_the_other_report(self):
        duplicate = next(r for r in self.results if r.verdict == "duplicate")
        for other in duplicate.clustered_with:
            self.assertNotIn(other, duplicate.reply_en)
            self.assertNotIn(other, duplicate.reply_zh)

    def test_patch_note_only_for_review_and_judgment(self):
        for result in self.all_results():
            with self.subTest(report=result.report.id, verdict=result.verdict):
                if result.verdict in PATCH_NOTE_VERDICTS:
                    self.assertIsNotNone(result.patch_note)
                    self.assertIsNone(result.patch_note_reason)
                else:
                    self.assertIsNone(result.patch_note)
                    self.assertTrue(result.patch_note_reason.startswith("No patch note:"))

    def test_patch_note_states_the_four_required_things(self):
        notes = [r for r in self.all_results() if r.patch_note]
        self.assertTrue(notes)
        for result in notes:
            note = result.patch_note
            with self.subTest(report=result.report.id):
                self.assertIn("Exploitability: not confirmed", note)
                self.assertIn("Where untrusted input enters:", note)
                self.assertIn("Path to fix: `%s`" % result.evidence.path, note)
                self.assertIn("separate security release", note)

    def test_entry_point_is_taken_from_the_report(self):
        first = next(r for r in self.results if r.verdict == "worth human review")
        self.assertIn("X-Filename", first.evidence.entry_point)
        self.assertIn("unverified", first.patch_note)


if __name__ == "__main__":
    unittest.main()
