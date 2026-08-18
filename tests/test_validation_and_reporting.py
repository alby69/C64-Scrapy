import os
import shutil
import tempfile
import unittest
from c64_scraper.utils.validator import ItemValidator
from c64_scraper.utils.reporter import RunReporter

class TestValidationAndReporting(unittest.TestCase):

    def test_item_validator_valid(self):
        item = {
            "url": "https://www.c64-wiki.com/wiki/C64",
            "title": "C64",
            "body_md": "Commodore 64 documentation",
            "scraped_at": "2026-01-01"
        }
        is_valid, err = ItemValidator.validate_item(item)
        self.assertTrue(is_valid)
        self.assertEqual(err, "")

    def test_item_validator_invalid_url(self):
        item = {
            "url": "invalid-url-string",
            "title": "C64",
            "body_md": "Commodore 64 documentation",
            "scraped_at": "2026-01-01"
        }
        is_valid, err = ItemValidator.validate_item(item)
        self.assertFalse(is_valid)

    def test_run_reporter(self):
        temp_dir = tempfile.mkdtemp()
        try:
            reporter = RunReporter(reports_dir=temp_dir)
            reporter.record_scraped("https://www.c64-wiki.com/wiki/C64")
            reporter.record_skipped("https://www.c64-wiki.com/wiki/MOS_6510")
            reporter.record_error("https://www.c64-wiki.com/wiki/ErrorPage", "HTTP 500")

            report = reporter.generate_report("c64wiki")
            self.assertEqual(report["items_scraped"], 1)
            self.assertEqual(report["items_skipped"], 1)
            self.assertEqual(report["errors_count"], 1)
            self.assertTrue(os.path.exists(os.path.join(temp_dir, "c64wiki_run_report.json")))
        finally:
            shutil.rmtree(temp_dir)

if __name__ == "__main__":
    unittest.main()
