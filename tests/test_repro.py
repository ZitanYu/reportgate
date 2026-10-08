"""The 0-3 reproduction score."""

import unittest

from reportgate import Report
from reportgate.repro import score_reproduction
from reportgate.text import split_code


def score(text):
    prose, blocks = split_code(text)
    return score_reproduction(prose, blocks).score


class ReproductionScore(unittest.TestCase):
    def test_0_nothing(self):
        self.assertEqual(score("The parser looks unsafe."), 0)

    def test_1_only_a_mention(self):
        self.assertEqual(score("I have a working PoC and can share it later."), 1)
        self.assertEqual(score("我可以复现这个问题。"), 1)

    def test_2_steps_without_code(self):
        self.assertEqual(score("1. Open the page.\n2. Click save.\n"), 2)

    def test_2_code_without_steps_or_payload(self):
        self.assertEqual(score("```\nparse(data)\n```"), 2)

    def test_3_code_plus_steps(self):
        self.assertEqual(score("1. Run it.\n2. Watch.\n\n```\nparse(data)\n```"), 3)

    def test_3_code_plus_payload(self):
        self.assertEqual(score("```\nopen('../../x')\n```"), 3)

    def test_steps_under_a_heading_with_bullets(self):
        self.assertEqual(score("Steps to reproduce:\n\n- start\n- send\n"), 2)

    def test_a_diff_is_not_a_reproduction(self):
        self.assertEqual(score("```diff\n- bad()\n+ good()\n```"), 0)

    def test_suggested_fix_section_is_not_scored(self):
        from reportgate.readers import read_markdown

        report: Report = read_markdown(
            "# t\n\nThe parser is unsafe.\n\n## Suggested fix\n\n```c\nfix();\n```\n", "r"
        )[0]
        self.assertNotIn("fix();", report.body)
        self.assertIn("fix();", report.suggested_fix)
        self.assertEqual(score(report.body), 0)


if __name__ == "__main__":
    unittest.main()
