import os
import json
import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class RunReporter:
    """Tracks spider execution metrics and generates a run report artifact."""

    def __init__(self, reports_dir: str = "dataset_c64/reports"):
        self.reports_dir = reports_dir
        self.start_time = time.time()
        self.scraped_count = 0
        self.updated_count = 0
        self.skipped_count = 0
        self.error_count = 0
        self.errors = []

    def record_scraped(self, url: str):
        self.scraped_count += 1

    def record_skipped(self, url: str, reason: str = "unmodified"):
        self.skipped_count += 1

    def record_error(self, url: str, error_msg: str):
        self.error_count += 1
        self.errors.append({"url": url, "error": error_msg})

    def generate_report(self, spider_name: str) -> Dict[str, Any]:
        duration = round(time.time() - self.start_time, 2)
        report = {
            "spider": spider_name,
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "duration_seconds": duration,
            "items_scraped": self.scraped_count,
            "items_skipped": self.skipped_count,
            "errors_count": self.error_count,
            "error_details": self.errors[:50]  # Limit error list size
        }

        os.makedirs(self.reports_dir, exist_ok=True)
        report_path = os.path.join(self.reports_dir, f"{spider_name}_run_report.json")
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"Execution report saved to {report_path}")
        except Exception as e:
            logger.error(f"Failed to write report to {report_path}: {e}")

        return report
