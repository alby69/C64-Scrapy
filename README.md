# C64 Documentation Scraper & Manual Generator

## 1. Obiettivo

Questo progetto è un framework basato su **Scrapy** per l'estrazione automatica di documentazione tecnica riguardante il Commodore 64 da vari siti web (es. elite.bbcelite.com, codebase64.org, ecc.).
L'obiettivo è generare:
- Una Knowledge Base in formato Markdown organizzata per cartelle, pronta per essere indicizzata in sistemi RAG (come [alby69/C64-LLM](https://github.com/alby69/C64-LLM)).
- Un manuale PDF unico, completo di codice Assembly e BASIC, generato tramite Pandoc.

## 2. Architettura

Il progetto è strutturato come un plugin per sistemi di Knowledge Management:
- **Spiders**: Ogni sito ha il suo spider dedicato in `c64_metadata/spiders/`.
- **Pipelines**: Gestiscono la pulizia dei dati e la scrittura dei file Markdown con frontmatter YAML.
- **Post-processing**: Script per la creazione di indici e la generazione di PDF.

## 3. Installazione

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# Richiede pandoc per la generazione PDF
```

## 4. Utilizzo

### Scraping
Per avviare lo scraping di una fonte specifica:
```bash
scrapy crawl bbcelite -s DOCS_OUTPUT_DIR=docs_c64
```

### Generazione Indice
```bash
python build_index.py --docs docs_c64
```

### Generazione PDF
```bash
python build_pdf.py --docs docs_c64 --out manuale_c64.pdf
```

## 5. Integrazione con C64-LLM

Questo repo può essere integrato come modulo in `C64-LLM`. I file Markdown prodotti sono compatibili con il sistema RAG di `C64-LLM`.
Consultare `INTEGRATION.md` per i dettagli tecnici sull'integrazione.
