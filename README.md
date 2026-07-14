# C64 Scraper Module

Componente dell'ecosistema **[C64-Intelligence-SDK](https://github.com/alby69/C64-Intelligence-SDK)** dedicato all'acquisizione di dati tecnici da siti web, libri, articoli, tutorial e newsgroup dedicati alla programmazione del Commodore 64 (specialmente in Assembly 6502 e BASIC).

## Filosofia & Architettura Decoupled (Integrazione con C64-KB-Agent)

Questo repository Scrapy è progettato per operare secondo il principio di **separazione delle responsabilità (Decoupling)**. Lo Scraper ha l'unico scopo di effettuare l'**estrazione e la conversione iniziale** dei documenti in file Markdown formattati con frontmatter YAML e record JSONL deterministici:

```
[ Web / Fonti Esterne ]
       │
       ▼ (Scrapy Spiders)
[ C64-Scrapy ] ─────────► Genera file .md con frontmatter YAML & record JSONL deterministici (con hash SHA256)
       │
       ▼ (Trasferimento dati)
[ C64-KB-Agent ] ───────► (https://github.com/alby69/C64-KB-Agent)
       │                  RAG & Knowledge Base Centralizzata:
       │                  - Deduplicazione intelligente (confronto ID SHA256 dei record)
       │                  - Memorizzazione e strutturazione avanzata della Knowledge Base
       │                  - Chunking semantico & Embedding vectoriali
       │
       ▼ (Query / Interrogazione)
  [ C64-LLM ]
```

### Ruoli del Flusso:
1. **C64-Scrapy (Questo Repo)**: Naviga le fonti (es. `codebase.c64.org`, `c64-wiki.com`, `elite.bbcelite.com`, `archive.org`, `github.com`), estrae il contenuto principale pulito, ne deduce metadati e linguaggio dei blocchi di codice (BASIC o Assembly), e produce i dataset in `docs_c64/` e `dataset_c64/scraped_dataset.jsonl` usando ID deterministici univoci basati su SHA256 dell'URL.
2. **C64-KB-Agent (RAG & KB Centralizzata)**: Prende in input i file estratti da questo modulo, gestisce l'eliminazione dei duplicati (evitando di reinserire record con lo stesso ID SHA256 o contenuto sovrapposto) e li organizza nella Knowledge Base ufficiale ottimizzata per essere interrogata dal LLM.

---

## Obiettivo dello Scraper

Questo modulo è un framework basato su **Scrapy** per l'estrazione automatica di documentazione tecnica, manuali e sorgenti riguardanti il Commodore 64. I dati estratti vengono convertiti in Markdown strutturato con metadati YAML, ottimizzati per:
1. **RAG (Retrieval-Augmented Generation)**: Alimentare la Knowledge Base di agenti AI (come `C64-LLM`) tramite `C64-KB-Agent`.
2. **Documentazione Offline**: Generare manuali PDF unificati tramite Pandoc.
3. **Analisi del Codice**: Estrarre snippet Assembly 6502 e BASIC per validazione e training.

## Architettura del Progetto

Il modulo è strutturato come segue:
- **Spiders**: Logica di navigazione specifica per ogni sito sorgente (`c64_scraper/spiders/`).
  - `bbcelite`: Estrae i dettagli tecnici e disassemblati di Elite C64.
  - `codebase64`: Crawling sistematico di `https://codebase.c64.org/`.
  - `c64wiki`: Estrazione sistematica da `c64-wiki.com`.
  - `archiveorg`: Metadata e dettagli da libri e manuali caricati su Archive.org.
  - `github`: Metadata di repository GitHub contenenti codice Assembly o BASIC per C64.
- **Content Processor**: Logica di pulizia e conversione centralizzata (`c64_scraper/utils/processor.py`).
- **Data Contract**: Ogni documento segue uno schema Markdown + YAML standard.

## Installazione

### Tramite Docker (Consigliato)

```bash
# Build dell'immagine
docker compose build

# Esecuzione di uno spider con generazione indice
docker compose run scraper codebase64 --index

# Esecuzione di tutti gli spider con indice e PDF
docker compose run scraper --all --pdf
```

### Installazione Locale

```bash
pip install -r requirements.txt
# Richiede pandoc per la generazione PDF opzionale
```

## Utilizzo

### Tramite Docker (Consigliato)

```bash
# Esegue uno spider e genera l'indice
docker compose run scraper codebase64 --index

# Esegue tutti gli spider, genera indice e PDF
docker compose run scraper --all --pdf

# Solo generazione indice (dopo aver eseguito gli spider)
docker compose run index

# Solo generazione PDF (dopo aver generato l'indice)
docker compose run pdf
```

### Tramite Entry Point (Installazione Locale)
```bash
# Esegue uno spider e genera l'indice
python main.py codebase64 --index

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

All'interno dell'SDK, questo modulo viene montato come volume Docker e i suoi output (`docs_c64/` o `dataset_c64/`) sono condivisi con il modulo centralizzato `C64-KB-Agent` per l'aggiornamento dinamico e la strutturazione avanzata della Knowledge Base.
