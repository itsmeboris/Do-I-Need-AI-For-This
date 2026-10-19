"""Regression checks for the public checker and report pipeline."""
import re
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "do-i-need-ai-for-this"
sys.path.insert(0, str(SKILL))
from check_verdict import check_verdict
from render_verdict import VerdictRenderError, render_file


class ReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.source = Path(self.temp.name) / "input.md"
        self.output = Path(self.temp.name) / "report.html"
        self.example = (ROOT / "examples/support-triage.md").read_text(encoding="utf-8")
        self.source.write_text(self.example, encoding="utf-8")

    def test_example_renders_expected_metrics(self):
        self.assertEqual(check_verdict(self.source), [])
        render_file(self.source, self.output, date(2026, 10, 19))
        html = self.output.read_text(encoding="utf-8")
        for metric in ('aria-label="1 judgment step"', 'aria-label="MID model tiers"', 'aria-label="Required Human gate"'):
            self.assertIn(metric, html)

    def test_empty_required_section_rejected(self):
        for section in ("Restated use case", "Frame", "Decomposition", "Failure modes", "Revisit when", "Next step"):
            with self.subTest(section=section):
                text = re.sub(r"(## " + re.escape(section) + r"\n).*?(?=\n## |\Z)", r"\1\n", self.example, flags=re.S)
                self.source.write_text(text, encoding="utf-8")
                self.assertTrue(check_verdict(self.source), section)

    def test_empty_section_cannot_replace_existing_report(self):
        self.output.write_text("previous report", encoding="utf-8")
        text = re.sub(r"(## Frame\n).*?(?=\n## )", r"\1\n", self.example, flags=re.S)
        self.source.write_text(text, encoding="utf-8")
        with self.assertRaises(VerdictRenderError):
            render_file(self.source, self.output)
        self.assertEqual(self.output.read_text(), "previous report")
        self.assertEqual(sorted(p.name for p in self.output.parent.iterdir()), ["input.md", "report.html"])

    def test_missing_tier_rejected(self):
        self.source.write_text(self.example.replace("MID - multiple plausible intents must be reconciled", "-"), encoding="utf-8")
        self.assertTrue(any(v.check == "model-tier" for v in check_verdict(self.source)))

    def test_report_explains_validation_scope(self):
        render_file(self.source, self.output)
        html = self.output.read_text(encoding="utf-8")
        self.assertIn("Structure checked", html)
        self.assertIn("does not establish that the recommendation is correct", html)
        self.assertNotIn(">Verified<", html)

    def test_untrusted_input_is_displayed_as_text(self):
        payload = '<script>alert(1)</script><img src="https://example.com/track">'
        self.source.write_text(self.example.replace("Support Triage Verdict", payload), encoding="utf-8")
        render_file(self.source, self.output)
        class Tags(HTMLParser):
            def __init__(self):
                super().__init__()
                self.tags = []
            def handle_starttag(self, tag, attrs):
                self.tags.append(tag)
        parser = Tags()
        html = self.output.read_text(encoding="utf-8")
        parser.feed(html)
        self.assertNotIn("script", parser.tags)
        self.assertNotIn("img", parser.tags)
        self.assertIn("&lt;script&gt;", html)

    def test_cli_rejects_invalid_input_without_creating_output(self):
        self.source.write_text("not a verdict", encoding="utf-8")
        for script, args in (("check_verdict.py", [self.source]), ("render_verdict.py", [self.source, self.output])):
            result = subprocess.run([sys.executable, str(SKILL / script), *map(str, args)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
