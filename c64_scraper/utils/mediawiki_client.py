import urllib.request
import urllib.parse
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class MediaWikiRestClient:
    """Client for interacting with MediaWiki REST API (v1)."""

    BASE_URL = "https://www.c64-wiki.com/rest.php/v1"

    def __init__(self, user_agent: str = "C64-Scrapy/1.0 (+https://github.com/alby69/C64-Scrapy)"):
        self.user_agent = user_agent

    def _get_json(self, url: str) -> Optional[Dict[str, Any]]:
        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    data = resp.read().decode("utf-8")
                    return json.loads(data)
        except Exception as e:
            logger.warning(f"Error fetching REST endpoint {url}: {e}")
        return None

    def _get_text(self, url: str) -> Optional[str]:
        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                if resp.status == 200:
                    return resp.read().decode("utf-8")
        except Exception as e:
            logger.warning(f"Error fetching REST endpoint {url}: {e}")
        return None

    def get_page_metadata(self, title: str) -> Optional[Dict[str, Any]]:
        """
        Fetches metadata for a given page title.
        Returns dict containing id, key, title, latest (id, timestamp), content_model, license, source (wikitext).
        """
        encoded_title = urllib.parse.quote(title)
        url = f"{self.BASE_URL}/page/{encoded_title}"
        return self._get_json(url)

    def get_page_html(self, title: str) -> Optional[str]:
        """
        Fetches Parsoid-rendered article body HTML without MediaWiki skin or navigation menus.
        """
        encoded_title = urllib.parse.quote(title)
        url = f"{self.BASE_URL}/page/{encoded_title}/html"
        return self._get_text(url)
