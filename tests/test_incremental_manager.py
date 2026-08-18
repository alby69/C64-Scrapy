import os
import shutil
import tempfile
import unittest
from c64_scraper.utils.incremental_manager import IncrementalStateManager

class TestIncrementalStateManager(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.manager = IncrementalStateManager(state_dir=self.temp_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir)

    def test_save_and_load_state(self):
        url = "https://www.c64-wiki.com/wiki/C64"
        timestamp = "2025-11-02T17:39:16Z"
        scraped_at = "2026-01-01"

        self.manager.update_page_state("c64wiki", url, timestamp, scraped_at)

        state = self.manager.load_state("c64wiki")
        self.assertIn("pages", state)
        self.assertIn(url, state["pages"])
        self.assertEqual(state["pages"][url]["last_modified"], timestamp)

        # Check unmodified check
        self.assertTrue(self.manager.is_page_unmodified("c64wiki", url, timestamp))
        self.assertFalse(self.manager.is_page_unmodified("c64wiki", url, "2026-01-01T00:00:00Z"))
        self.assertFalse(self.manager.is_page_unmodified("c64wiki", "https://other.url", timestamp))

if __name__ == "__main__":
    unittest.main()
