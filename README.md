# C64 Scraper Module

Componente dell'ecosistema **[C64-Intelligence-SDK](https://github.com/alby69/C64-Intelligence-SDK)** dedicato all'acquisizione e alla validazione di dati tecnici da siti web, libri, articoli, tutorial e newsgroup dedicati alla programmazione del Commodore 64 (Assembly 6502/6510 e BASIC).

## Filosofia & Architettura Decoupled (Integrazione con C64-KB-Agent)

Questo repository Scrapy è progettato per operare secondo il principio di **separazione delle responsabilità (Decoupling)**. Lo Scraper effettua l'estrazione, la conversione e la validazione iniziale dei documenti in file Markdown formattati con frontmatter YAML e record JSONL deterministici:

```
[ Web / Fonti Esterne ]
       │
       ▼ (Scrapy Spiders)
[ C64-Scrapy ] ─────────► Genera file .md con frontmatter YAML, manifest KB e record JSONL deterministici (con hash SHA256)
       │                  - Detection dialetto Assembly (ACME, DASM, KickAssembler, CA65, Turbo Assembler)
       │                  - Validazione sintattica 6502/6510 (inclusi illegal opcodes) & C64 BASIC
       │                  - Notifica webhook & Manifest di sincronizzazione
       │
       ▼ (Trasferimento dati / Webhook)
[ C64-KB-Agent ] ───────► (https://github.com/alby69/C64-KB-Agent)
       │                  RAG & Knowledge Base Centralizzata:
       │                  - Deduplicazione intelligente (confronto ID SHA256 dei record)
       │                  - Memorizzazione e strutturazione avanzata della Knowledge Base
       │                  - Chunking semantico & Embedding vettoriali
       │
       ▼ (Query / Interrogazione)
  [ C64-LLM ]
```

---

## Funzionalità Principali

1. **Riconoscimento Dialetti Assembly & Validazione Sintattica**:
   - Identificazione automatica di assembler target: **Kick Assembler, ACME, DASM, CA65, Turbo Assembler**.
   - Validazione della correttezza formale per codice Assembly 6502/6510 (inclusi illegal opcodes come `LAX`, `SAX`, `DCP`, `ISC`, `SLO`, `RLA`, `SRE`) e C64 BASIC.
2. **Scraping Incrementale Diff**:
   - Gestione persistente dello stato (`dataset_c64/state/`) per scaricare solo pagine create o modificate di recente (via HTTP `Last-Modified` o revision ID).
3. **Generazione Sync Manifest & Webhook Notification**:
   - Produzione automatica di `dataset_c64/kb_sync_manifest.json` e invio di notifiche HTTP POST a `C64-KB-Agent`.
4. **Scraping On-Demand**:
   - Invocazione diretta per singolo URL via `python main.py scrape-url <URL>` con auto-routing automatico dello spider in base al dominio.

---

## Spiders Supportati

- `c64wiki`: Estrazione da [C64-Wiki](https://www.c64-wiki.com/).
- `codebase64`: Crawling di [Codebase64](https://codebase.c64.org/).
- `bbcelite`: Disassemblato e guide tecniche di Elite C64.
- `dustlayer`: Tutorial approfonditi per VIC-II e programmazione C64.
- `stac64`: Mappe di memoria e documentazione hardware da `sta.c64.org`.
- `archiveorg`: Metadata da libri e manuali su Archive.org.
- `github`: Repository e campioni di codice Assembly C64 da GitHub.

---

## Installazione e Utilizzo

### Tramite Docker (Consigliato)

```bash
# Build dell'immagine
docker compose build

# Esecuzione di tutti gli spider in modalità incrementale con indice e notifica KB
docker compose run scraper --all --incremental --index --notify-kb
```

### Installazione Locale

```bash
pip install -r requirements.txt

# Scraping completo di tutti gli spider
python main.py --all --index --notify-kb

# Scraping incrementale di uno specifico spider
python main.py c64wiki --incremental --index

# On-demand scraping di un singolo URL (routing automatico dello spider)
python main.py scrape-url "https://www.c64-wiki.com/wiki/VIC-II" --notify-kb
```

---

## CI/CD Pipeline

Il workflow GitHub Actions `.github/workflows/scrape-and-sync.yml` esegue lo scraping programmato e sincronizza i dati su `C64-KB-Agent`:

```yaml
env:
  KB_AGENT_TOKEN: ${{ secrets.KB_AGENT_TOKEN }}
  KB_WEBHOOK_URL: ${{ secrets.KB_WEBHOOK_URL }}
```
