import tempfile
import pathlib
import sqlite3
import json
import pytest
from c64_scraper.utils.processor import ContentProcessor
from build_knowledge_graph import build_knowledge_graph
from build_search_index import build_search_index
from build_api_index import build_api_index

def test_classify_document():
    # Test VIC-II / graphics classification
    title = "VIC-II Sprite Programming for Beginners"
    body = "In this tutorial we will learn how to enable sprites using $D015 register and set border color $D020. lda #$01 sta $d020 rts"
    classification = ContentProcessor.classify_document("", body, "http://example.com/sprite_tutorial", title, "dustlayer")

    assert classification["category"] == "tutorial"
    assert "VIC-II" in classification["hardware"]
    assert "sprite programming" in classification["topics"]
    assert classification["difficulty"] == "beginner"
    assert classification["language"] == "assembly"

    # Test SID / music classification
    title = "Advanced SID music player coding"
    body = "We use complex timing and envelope filters around $D400 memory."
    classification = ContentProcessor.classify_document("", body, "http://example.com/sid_music", title, "bbcelite")

    assert classification["category"] == "reference" # bbcelite defaults to reference if no other cues
    assert "SID" in classification["hardware"]
    assert "sound generation" in classification["topics"]
    assert classification["difficulty"] == "advanced"

def test_detect_assembly_dialect():
    # Kick Assembler
    code_kick = """
    .pc = $c000
    .const border = $d020
    lda #$01
    sta border
    rts
    """
    assert ContentProcessor.detect_assembly_dialect(code_kick) == "Kick Assembler"

    # ACME
    code_acme = """
    !to "main.prg", cbm
    * = $c000
    lda #$01
    sta $d020
    rts
    """
    assert ContentProcessor.detect_assembly_dialect(code_acme) == "ACME"

    # DASM
    code_dasm = """
    processor 6502
    org $c000
    lda #$01
    sta $d020
    rts
    """
    assert ContentProcessor.detect_assembly_dialect(code_dasm) == "DASM"

def test_extract_routines_from_code():
    code = """
    ; This is a print string helper routine
    ; Inputs: None
    ; Outputs: Prints a message
    print_msg:
        lda #$01
        sta $d020
        rts

    // This is the main program starting point
    main_init:
        jsr print_msg
        rts
    """
    routines = ContentProcessor.extract_routines_from_code(code, "http://test.url")
    assert len(routines) == 2

    r1 = [r for r in routines if r["name"] == "print_msg"][0]
    assert "print string helper" in r1["description"]

    r2 = [r for r in routines if r["name"] == "main_init"][0]
    assert "main program starting point" in r2["description"]

def test_pipelines_build_indexes():
    # Create a temporary directory structure and test building indexes, graph, DB
    with tempfile.TemporaryDirectory() as tmpdir:
        docs_path = pathlib.Path(tmpdir) / "docs"
        docs_path.mkdir()

        # Write dummy file with frontmatter
        dummy_md = docs_path / "dummy_doc.md"
        dummy_md_content = """---
title: "VIC-II Interrupt Tutorial"
source_url: "http://example.com/interrupt"
category: "tutorial"
topics: ["raster interrupts"]
difficulty: "beginner"
language: "assembly"
hardware: ["VIC-II"]
related: ["raster-interrupts"]
scraped_at: "2024-01-01"
---
# VIC-II Interrupt Tutorial

In this tutorial we will read $D012 register to check the raster counter.

```assembly
; Our raster interrupt callback
irq_handler:
    inc $d020
    jmp $ea31
```
"""
        dummy_md.write_text(dummy_md_content, encoding="utf-8")

        # Test Knowledge Graph Generation
        kg_json = pathlib.Path(tmpdir) / "knowledge_graph.json"
        build_knowledge_graph(docs_path, kg_json)

        assert kg_json.exists()
        graph = json.loads(kg_json.read_text(encoding="utf-8"))
        assert len(graph["nodes"]) > 0
        assert len(graph["edges"]) > 0

        # Ensure cross-reference links were injected back into md
        new_content = dummy_md.read_text(encoding="utf-8")
        assert "### Collegamenti e Riferimenti Hardware" in new_content
        assert "$D012" in new_content
        assert "$D020" in new_content

        # Test SQLite search index build
        db_path = pathlib.Path(tmpdir) / "search_index.db"
        build_search_index(docs_path, db_path)

        assert db_path.exists()
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Check documents
        cursor.execute("SELECT id, title, category FROM documents")
        docs = cursor.fetchall()
        assert len(docs) == 1
        assert docs[0][1] == "VIC-II Interrupt Tutorial"

        # Check routines
        cursor.execute("SELECT name, doc_id FROM routines")
        routines = cursor.fetchall()
        assert len(routines) == 1
        assert routines[0][0] == "irq_handler"

        conn.close()

        # Test API Index Generation
        api_json = pathlib.Path(tmpdir) / "api_index.json"
        build_api_index(docs_path, api_json)

        assert api_json.exists()
        api_data = json.loads(api_json.read_text(encoding="utf-8"))
        assert len(api_data) == 1
        assert api_data[0]["title"] == "VIC-II Interrupt Tutorial"
        assert len(api_data[0]["code_snippets"]) == 1
        assert len(api_data[0]["routines"]) == 1
        assert api_data[0]["routines"][0]["name"] == "irq_handler"
