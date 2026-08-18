import unittest
from unittest.mock import MagicMock, patch
from c64_scraper.utils.mediawiki_client import MediaWikiRestClient

class TestMediaWikiRestClient(unittest.TestCase):

    @patch("urllib.request.urlopen")
    def test_get_page_metadata(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'{"id": 1414, "key": "C64", "title": "C64", "latest": {"id": 43607, "timestamp": "2025-11-02T17:39:16Z"}, "license": {"title": "GFDL"}}'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        client = MediaWikiRestClient()
        meta = client.get_page_metadata("C64")
        self.assertIsNotNone(meta)
        self.assertEqual(meta["title"], "C64")
        self.assertEqual(meta["latest"]["id"], 43607)
        self.assertEqual(meta["license"]["title"], "GFDL")

    @patch("urllib.request.urlopen")
    def test_get_page_html(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = b'<html><body><p>Test content</p></body></html>'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        client = MediaWikiRestClient()
        html = client.get_page_html("C64")
        self.assertIsNotNone(html)
        self.assertIn("Test content", html)

if __name__ == "__main__":
    unittest.main()
