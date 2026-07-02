# Integrazione con C64-LLM

Questo repository è progettato per funzionare come un modulo esterno o plugin per il progetto [alby69/C64-LLM](https://github.com/alby69/C64-LLM).

## Modalità di Integrazione

### 1. Come sorgente per la Knowledge Base (RAG)
I file Markdown generati da questo scraper includono il frontmatter YAML richiesto dal sistema RAG di C64-LLM.

**Passaggi per l'integrazione:**
1. Eseguire lo scraper per generare i documenti:
   ```bash
   scrapy crawl bbcelite -s DOCS_OUTPUT_DIR=./docs_c64
   ```
2. Copiare i documenti nella cartella `knowledge_base` di C64-LLM:
   ```bash
   cp -r docs_c64/* /path/to/C64-LLM/knowledge_base/
   ```
3. Avviare l'indicizzazione in C64-LLM:
   ```bash
   docker compose run --rm c64-pipeline python agent/knowledge_base.py
   ```

### 2. Come Plugin Docker
È possibile aggiungere questo scraper nel `docker-compose.yml` di C64-LLM come servizio aggiuntivo per automatizzare l'aggiornamento della documentazione.

### 3. Generazione di Manuali Personalizzati per Distiller
Il Distiller di C64-LLM può trarre beneficio dai documenti tecnici estratti per generare coppie di domande/risposte (Q&A) di alta qualità. L'inclusione di blocchi di codice Assembly/BASIC estratti esplicitamente facilita il fine-tuning dei modelli.

## Specifiche Tecniche per lo Sviluppatore di C64-LLM

Se desideri integrare questo codice direttamente nel repo principale:
- Sposta la cartella `c64_metadata` in `C64-LLM/pipeline/`.
- Unifica le dipendenze in `requirements.txt`.
- Lo spider `bbcelite.py` può essere affiancato a `c64_asm_scraper.py`.

## Formato dei Dati
Ogni file generato segue questo schema:
```yaml
---
title: "Titolo Pagina"
source_url: "https://..."
category: "categoria"
tags: [c64, assembly]
scraped_at: "YYYY-MM-DD"
---
# Titolo

Contenuto in Markdown...
```
