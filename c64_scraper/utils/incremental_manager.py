import os
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class IncrementalStateManager:
    """Manages spider state persistence for incremental scraping runs."""

    def __init__(self, state_dir: str = "dataset_c64/state"):
        self.state_dir = state_dir
        self.cache: Dict[str, Dict[str, Any]] = {}

    def _get_state_filepath(self, spider_name: str) -> str:
        return os.path.join(self.state_dir, f"{spider_name}_last_run.json")

    def load_state(self, spider_name: str) -> Dict[str, Any]:
        if spider_name in self.cache:
            return self.cache[spider_name]

        filepath = self._get_state_filepath(spider_name)
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    state = json.load(f)
                    self.cache[spider_name] = state
                    return state
            except Exception as e:
                logger.warning(f"Failed to load state from {filepath}: {e}")

        state = {"pages": {}}
        self.cache[spider_name] = state
        return state

    def save_state(self, spider_name: str) -> bool:
        if spider_name not in self.cache:
            return False

        os.makedirs(self.state_dir, exist_ok=True)
        filepath = self._get_state_filepath(spider_name)
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self.cache[spider_name], f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Failed to save state to {filepath}: {e}")
            return False

    def is_page_unmodified(self, spider_name: str, url: str, last_modified_timestamp: Optional[str]) -> bool:
        """
        Checks if a given page URL has not been modified since the last recorded run.
        """
        if not last_modified_timestamp:
            return False

        state = self.load_state(spider_name)
        pages_state = state.get("pages", {})
        last_recorded = pages_state.get(url, {}).get("last_modified")

        if last_recorded and last_recorded == last_modified_timestamp:
            return True

        return False

    def update_page_state(self, spider_name: str, url: str, last_modified_timestamp: Optional[str], scraped_at: str) -> None:
        state = self.load_state(spider_name)
        if "pages" not in state:
            state["pages"] = {}

        state["pages"][url] = {
            "last_modified": last_modified_timestamp,
            "scraped_at": scraped_at
        }
