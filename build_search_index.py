#!/usr/bin/env python3
import pathlib
import sqlite3
import yaml
import re
from c64_scraper.utils.processor import ContentProcessor

def read_frontmatter_and_body(md_path: pathlib.Path):
    try:
        text = md_path.read_text(encoding="utf-8")
        if not text.startswith("---"):
            return {}, text
        parts = text.split("---", 2)
        if len(parts) >= 3:
            return yaml.safe_load(parts[1]) or {}, parts[2]
        return {}, text
    except Exception:
        return {}, ""

def extract_code_blocks_from_md(md_text: str) -> list:
    pattern = r"```([a-zA-Z0-9_\-+]*)\n(.*?)\n```"
    blocks = []
    for match in re.finditer(pattern, md_text, re.DOTALL):
        lang = match.group(1).strip()
        code = match.group(2).strip()
        blocks.append({"lang": lang, "code": code})
    return blocks

def build_search_index(docs_dir: pathlib.Path, db_path: pathlib.Path):
    if not docs_dir.exists():
        print(f"[avviso] la cartella {docs_dir} non esiste. Impossibile creare l'indice di ricerca.")
        return

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Drop tables to recreate cleanly
    cursor.execute("DROP TABLE IF EXISTS documents_fts;")
    cursor.execute("DROP TABLE IF EXISTS documents;")
    cursor.execute("DROP TABLE IF EXISTS routines;")

    # Recreate tables
    cursor.execute("""
    CREATE TABLE documents (
        id TEXT PRIMARY KEY,
        filepath TEXT,
        title TEXT,
        source_url TEXT,
        category TEXT,
        difficulty TEXT,
        language TEXT,
        hardware TEXT,
        topics TEXT,
        body TEXT
    );
    """)

    cursor.execute("""
    CREATE VIRTUAL TABLE documents_fts USING fts5(
        id,
        title,
        category,
        difficulty,
        language,
        hardware,
        topics,
        body
    );
    """)

    cursor.execute("""
    CREATE TABLE routines (
        name TEXT,
        address TEXT,
        description TEXT,
        source_url TEXT,
        doc_id TEXT
    );
    """)

    doc_count = 0
    routine_count = 0

    for md_path in sorted(docs_dir.rglob("*.md")):
        if md_path.name in ["index.md", "_combined.md"]:
            continue

        fm, body = read_frontmatter_and_body(md_path)
        if not fm:
            continue

        doc_id = md_path.relative_to(docs_dir).as_posix()
        title = fm.get("title", md_path.stem)
        url = fm.get("source_url", "")
        category = fm.get("category", "reference")
        difficulty = fm.get("difficulty", "intermediate")
        language = fm.get("language", "none")
        hardware = ", ".join(fm.get("hardware", []))
        topics = ", ".join(fm.get("topics", []))

        # Insert into documents table
        cursor.execute("""
        INSERT INTO documents (id, filepath, title, source_url, category, difficulty, language, hardware, topics, body)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (doc_id, doc_id, title, url, category, difficulty, language, hardware, topics, body))

        # Insert into FTS5
        cursor.execute("""
        INSERT INTO documents_fts (id, title, category, difficulty, language, hardware, topics, body)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (doc_id, title, category, difficulty, language, hardware, topics, body))

        doc_count += 1

        # Extract code routines and insert
        code_blocks = extract_code_blocks_from_md(body)
        for block in code_blocks:
            code_text = block["code"]
            lang = block["lang"]
            if lang in ["asm", "assembly"]:
                routines = ContentProcessor.extract_routines_from_code(code_text, url)
                for r in routines:
                    cursor.execute("""
                    INSERT INTO routines (name, address, description, source_url, doc_id)
                    VALUES (?, ?, ?, ?, ?);
                    """, (r["name"], r["address"], r["description"], r["source_url"], doc_id))
                    routine_count += 1

    conn.commit()
    conn.close()
    print(f"SQLite FTS5 Search Index creato con successo: {db_path} ({doc_count} documenti, {routine_count} routine indicizzate)")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Costruisce l'indice di ricerca SQLite FTS5")
    parser.add_argument("--docs", default="docs_c64", help="Cartella con i file Markdown")
    parser.add_argument("--db", default="dataset_c64/search_index.db", help="File DB SQLite di output")
    args = parser.parse_args()
    build_search_index(pathlib.Path(args.docs), pathlib.Path(args.db))
