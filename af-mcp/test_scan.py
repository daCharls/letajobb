#!/usr/bin/env python3
"""Regressionstester för scan.py + pipeline_lib.py.

    python af-mcp/test_scan.py

Kör mot en temporär kopia av en nybyggd pipeline (af-mcp/init.py:s mall),
rör aldrig din riktiga pipeline.html. Kräver inget nätverk.
"""

from __future__ import annotations

import asyncio
import io
import shutil
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))

import init  # noqa: E402
import pipeline_lib  # noqa: E402
import scan  # noqa: E402

PORTALS = """\
title_filter:
  positive: []
  negative: []
platsbanken:
  municipality: ""
  default_city: "Testort"
  searches:
    - {q: "a", category: tech}
    - {q: "b", category: komm}
"""


def _ad(ad_id: int, headline: str = "IT-support", employer: str = "Bolag AB") -> dict:
    return {"id": ad_id, "headline": headline, "employer": {"name": employer},
            "workplace_address": {"city": "Testort"}}


class ScanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "data").mkdir()
        self.html = self.tmp / "pipeline.html"
        self.html.write_text(init._build_pipeline_html(), encoding="utf-8")
        self.md = self.tmp / "data" / "pipeline.md"
        self.md.write_text("# Pipeline\n\n## Pendientes\n", encoding="utf-8")
        self.hist = self.tmp / "data" / "scan-history.tsv"
        self.hist.write_text("url\tfirst_seen\tportal\ttitle\tcompany\tstatus\n", encoding="utf-8")
        portals = self.tmp / "portals.yml"
        portals.write_text(PORTALS, encoding="utf-8")
        self._saved = {k: getattr(scan, k) for k in
                       ("PIPELINE_HTML", "PIPELINE_MD", "SCAN_HISTORY", "PORTALS_YML", "ROOT", "_search")}
        scan.PIPELINE_HTML, scan.PIPELINE_MD, scan.SCAN_HISTORY = self.html, self.md, self.hist
        scan.PORTALS_YML, scan.ROOT = portals, self.tmp

    def tearDown(self) -> None:
        for k, v in self._saved.items():
            setattr(scan, k, v)
        shutil.rmtree(self.tmp)

    def _run(self, results):
        """results: lista med (hits eller None) per sökning, i ordning."""
        it = iter(results)

        async def fake_search(*_a, **_k):
            return next(it)

        scan._search = fake_search
        out, err = io.StringIO(), io.StringIO()
        code = 0
        with redirect_stdout(out), redirect_stderr(err):
            try:
                asyncio.run(scan.main(7, False, False))
            except SystemExit as e:
                code = e.code or 0
        return code, out.getvalue(), err.getvalue()

    def test_happy_path_writes_all_three_files(self):
        code, _, _ = self._run([[_ad(1)], [_ad(2)]])
        self.assertEqual(code, 0)
        html = self.html.read_text(encoding="utf-8")
        self.assertEqual(pipeline_lib.count_jobs(html)["total"], 2)
        self.assertEqual(pipeline_lib.verify_pipeline(html), [])
        self.assertIn("/annonser/1", self.hist.read_text(encoding="utf-8"))

    def test_headline_is_html_escaped(self):
        self._run([[_ad(1, "Sales & Support <Remote>", "A&B <AB>")], []])
        html = self.html.read_text(encoding="utf-8")
        self.assertNotIn("<Remote>", html)
        self.assertIn("Sales &amp; Support &lt;Remote&gt;", html)
        self.assertIn("A&amp;B &lt;AB&gt;", html)
        self.assertEqual(pipeline_lib.verify_pipeline(html), [])

    def test_refused_write_does_not_mark_jobs_as_known(self):
        # Trasig struktur -> safe_write vägrar. Historiken får då INTE ha jobbet,
        # annars försvinner det för gott (buggen före 2026-10-11).
        broken = self.html.read_text(encoding="utf-8").replace("<!-- EJ AKTUELLA -->", "")
        self.html.write_text(broken, encoding="utf-8")
        code, _, _ = self._run([[_ad(333)], []])
        self.assertEqual(code, 1)
        self.assertNotIn("333", self.hist.read_text(encoding="utf-8"))
        self.assertNotIn("333", self.md.read_text(encoding="utf-8"))

    def test_all_searches_failing_is_an_error(self):
        code, out, err = self._run([None, None])
        self.assertEqual(code, 2)
        self.assertNotIn("Inga nya jobb", out)
        self.assertIn("Alla 2 sökningar misslyckades", err)

    def test_partial_failure_warns_but_continues(self):
        code, _, err = self._run([None, [_ad(5)]])
        self.assertEqual(code, 0)
        self.assertIn("1 av 2 sökningar misslyckades", err)
        self.assertEqual(pipeline_lib.count_jobs(self.html.read_text(encoding="utf-8"))["total"], 1)

    def test_backups_in_same_second_do_not_collide(self):
        a = pipeline_lib.backup_pipeline(self.html)
        b = pipeline_lib.backup_pipeline(self.html)
        self.assertNotEqual(a, b)
        self.assertTrue(a.exists() and b.exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
