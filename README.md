# C64 Scraper Module

Componente dell'ecosistema **[C64-Intelligence-SDK](https://github.com/alby69/C64-Intelligence-SDK)** dedicato all'acquisizione di dati tecnici.

## Obiettivo

Questo modulo è un framework basato su **Scrapy** per l'estrazione automatica di documentazione tecnica, manuali e sorgenti riguardanti il Commodore 64. I dati estratti vengono convertiti in Markdown strutturato con metadati YAML, ottimizzati per:
1. **RAG (Retrieval-Augmented Generation)**: Alimentare la Knowledge Base di agenti AI (come `C64-LLM`).
2. **Documentazione Offline**: Generare manuali PDF unificati tramite Pandoc.
3. **Analisi del Codice**: Estrarre snippet Assembly 6502 e BASIC per validazione e training.

## Architettura Decoupled

Il modulo è progettato per essere totalmente indipendente:
- **Spiders**: Logica di navigazione specifica per sito (`c64_scraper/spiders/`).
- **Content Processor**: Logica di pulizia e conversione centralizzata (`c64_scraper/utils/processor.py`).
- **Data Contract**: Ogni documento segue uno schema Markdown + YAML standard.

## Installazione

```bash
pip install -r requirements.txt
# Richiede pandoc per la generazione PDF
```

## Utilizzo

### Tramite Entry Point (Consigliato)
```bash
# Esegue uno spider e genera l'indice
python main.py bbcelite --index

# Esegue tutti gli spider, genera indice e PDF
python main.py --all --pdf
```

### Comandi Scrapy Standalone
```bash
scrapy crawl codebase64 -s DOCS_OUTPUT_DIR=docs_c64
```

## Schema dei Dati (Frontmatter)

I file generati includono metadati utili per l'indicizzazione:
```yaml
---
title: "Nome Pagina"
source_url: "https://..."
category: "sottocartella/argomento"
tags: [c64, assembly, graphics]
scraped_at: "YYYY-MM-DD"
---
```

## Integrazione SDK

All'interno dell'SDK, questo modulo viene montato come volume Docker e i suoi output (`docs_c64/`) sono condivisi con il modulo `core` per l'aggiornamento dinamico della Knowledge Base.
