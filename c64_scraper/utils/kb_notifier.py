import os
import json
import time
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import urllib.request
import urllib.error

logger = logging.getLogger(__name__)

class C64KBNotifier:
    """
    Generates sync manifests for downstream C64-KB-Agent ingestion
    and handles HTTP webhook notifications.
    """

    def __init__(self, dataset_dir: str = "dataset_c64", docs_dir: str = "docs_c64"):
        self.dataset_dir = Path(dataset_dir)
        self.docs_dir = Path(docs_dir)

    def generate_manifest(self, spiders_executed: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Generates a sync manifest artifact summarizing scraping status and records.
        """
        spiders_executed = spiders_executed or []

        total_docs = 0
        if self.docs_dir.is_dir():
            total_docs = len(list(self.docs_dir.rglob("*.md")))

        dataset_records = 0
        dataset_file = self.dataset_dir / "scraped_dataset.jsonl"
        if dataset_file.is_file():
            with open(dataset_file, "r", encoding="utf-8") as f:
                dataset_records = sum(1 for line in f if line.strip())

        spider_reports = {}
        reports_dir = self.dataset_dir / "reports"
        if reports_dir.is_dir():
            for report_file in reports_dir.glob("*_run_report.json"):
                try:
                    data = json.loads(report_file.read_text(encoding="utf-8"))
                    spider_name = data.get("spider", report_file.stem)
                    spider_reports[spider_name] = data
                except Exception as e:
                    logger.warning(f"Error reading report {report_file}: {e}")

        manifest = {
            "version": "1.0",
            "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "spiders_executed": spiders_executed,
            "metrics": {
                "total_docs_files": total_docs,
                "dataset_jsonl_records": dataset_records,
            },
            "spider_reports": spider_reports
        }

        self.dataset_dir.mkdir(parents=True, exist_ok=True)
        manifest_path = self.dataset_dir / "kb_sync_manifest.json"
        try:
            with open(manifest_path, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)
            logger.info(f"Sync manifest generated at {manifest_path}")
        except Exception as e:
            logger.error(f"Failed to write sync manifest: {e}")

        return manifest

    @staticmethod
    def send_webhook_notification(webhook_url: str, manifest: Dict[str, Any], token: Optional[str] = None) -> bool:
        """
        Sends an HTTP POST notification to C64-KB-Agent webhook endpoint.
        """
        if not webhook_url:
            logger.warning("No webhook URL provided for notification.")
            return False

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "C64-Scrapy-Notifier/1.0"
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"

        payload = json.dumps(manifest).encode("utf-8")
        req = urllib.request.Request(webhook_url, data=payload, headers=headers, method="POST")

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                if 200 <= resp.status < 300:
                    logger.info(f"Webhook notification sent successfully to {webhook_url}")
                    return True
                else:
                    logger.warning(f"Webhook endpoint returned status code {resp.status}")
                    return False
        except Exception as e:
            logger.error(f"Failed to send webhook notification to {webhook_url}: {e}")
            return False
