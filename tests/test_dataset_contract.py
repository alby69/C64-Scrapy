"""Test del contratto dati lato produttore (B2).

C64-Scrapy produce i documenti; ogni documento generato deve essere conforme
allo schema condiviso (in kb-agent/schemas/) PRIMA del push automatico verso
C64-KB-Agent. Il riferimento allo schema avviene per file (JSON), non per
import di codice: il contratto resta l'unico artefatto condiviso.
"""

import json
import os
from pathlib import Path

import pytest

BASE = Path(__file__).resolve().parent.parent
SCHEMA_PATH = BASE.parent / "kb-agent" / "schemas" / "document.schema.json"

try:
    import jsonschema
    from jsonschema import validate
except ImportError:  # pragma: no cover
    pytest.skip("jsonschema non installato", allow_module_level=True)


@pytest.fixture(scope="module")
def document_schema() -> dict:
    if not SCHEMA_PATH.is_file():
        pytest.skip(f"schema non trovato: {SCHEMA_PATH}")
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _frontmatter(text: str):
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    import yaml
    return yaml.safe_load(parts[1]) or {}


class TestGeneratedDocumentsValid:
    """Un documento prodotto dal flusso di scraping deve rispettare lo schema."""

    def test_fixture_document_valid(self, document_schema):
        fixture = _frontmatter(
            "---\n"
            "title: Sprite Programming\n"
            "source_url: https://example.com/sprite\n"
            "category: tutorial\n"
            "topics: [sprite programming, assembly]\n"
            "difficulty: beginner\n"
            "language: assembly\n"
            "hardware: [VIC-II]\n"
            "related: [vic-ii-registers]\n"
            "scraped_at: '2026-07-14'\n"
            "---\n"
            "# Sprite Programming\n"
        )
        validate(instance=fixture, schema=document_schema)

    def test_any_real_dataset_doc_valid(self, document_schema):
        """Se il dataset locale è presente, valida il primo documento reale."""
        docs_dir = BASE.parent / "kb-agent" / "data" / "docs"
        candidates = sorted(docs_dir.rglob("*.md")) if docs_dir.is_dir() else []
        if not candidates:
            pytest.skip("dataset locale non presente")
        import yaml
        doc = candidates[0]
        text = doc.read_text(encoding="utf-8")
        fm = _frontmatter(text)
        validate(instance=fm, schema=document_schema)


class TestSchemaDriftDetection:
    """Cambi di campo nello schema devono far fallire documenti obsoleti."""

    def test_unknown_category_rejected(self, document_schema):
        doc = {
            "title": "X", "source_url": "https://example.com/x",
            "category": "not-a-real-category", "topics": ["t"],
            "difficulty": "beginner", "language": "assembly",
            "hardware": [], "related": [], "scraped_at": "2026-01-01",
        }
        with pytest.raises(jsonschema.ValidationError):
            validate(instance=doc, schema=document_schema)

    def test_missing_required_field_rejected(self, document_schema):
        doc = {"title": "X", "category": "reference"}
        with pytest.raises(jsonschema.ValidationError):
            validate(instance=doc, schema=document_schema)