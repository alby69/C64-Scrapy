import json
import pytest
from c64_scraper.utils.kb_notifier import C64KBNotifier

def test_generate_manifest(tmp_path):
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()
    (docs_dir / "test1.md").write_text("# Test 1", encoding="utf-8")
    (docs_dir / "test2.md").write_text("# Test 2", encoding="utf-8")

    dataset_dir = tmp_path / "dataset"
    dataset_dir.mkdir()
    dataset_file = dataset_dir / "scraped_dataset.jsonl"
    dataset_file.write_text('{"id":"1"}\n{"id":"2"}\n', encoding="utf-8")

    reports_dir = dataset_dir / "reports"
    reports_dir.mkdir()
    (reports_dir / "c64wiki_run_report.json").write_text(json.dumps({
        "spider": "c64wiki",
        "items_scraped": 2
    }), encoding="utf-8")

    notifier = C64KBNotifier(dataset_dir=str(dataset_dir), docs_dir=str(docs_dir))
    manifest = notifier.generate_manifest(spiders_executed=["c64wiki"])

    assert manifest["version"] == "1.0"
    assert manifest["metrics"]["total_docs_files"] == 2
    assert manifest["metrics"]["dataset_jsonl_records"] == 2
    assert "c64wiki" in manifest["spider_reports"]
    assert (dataset_dir / "kb_sync_manifest.json").exists()
