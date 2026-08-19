# Roadmap - C64 Scraper

Questo documento delinea l'evoluzione del modulo Scraper all'interno dell'ecosistema C64 Intelligence SDK.

## Filosofia Decoupled

In accordo con l'architettura generale dell'SDK, il modulo **C64-Scrapy** si limita a compiti di:
- **Scraping ed estrazione di dati puliti** dal web (siti di riferimento, libri, tutorial, forum).
- **Conversione dei contenuti in Markdown standard** con frontmatter YAML.
- **Rilevamento, isolamento e validazione dei blocchi di codice** (Assembly 6502/6510 e C64 BASIC).
- **Generazione di record JSONL deterministici** dotati di ID SHA256 univoco basato sull'URL della risorsa.

Tutti i compiti di **strutturazione avanzata, memorizzazione vettoriale, chunking, deduplicazione e controllo di consistenza** sono delegati all'agente centralizzato **[C64-KB-Agent](https://github.com/alby69/C64-KB-Agent)**.

---

## Obiettivi Completati (Stato Attuale)

- [x] **Nuovi Spider**:
    - [x] `c64wiki`: Estrazione sistematica da [C64-Wiki](https://www.c64-wiki.com/).
    - [x] `codebase64`: Corretto dominio e start url su `https://codebase.c64.org/`.
    - [x] `archiveorg`: Estrazione di metadati e testi da Archive.org.
    - [x] `github`: Ricerca automatica di repository con assembly C64.
    - [x] `bbcelite`, `dustlayer`, `stac64`: Supporto esteso a portali e disassemblati di riferimento.
- [x] **Docker & Containerizzazione**:
    - [x] `Dockerfile` multi-stage con Python, pandoc e texlive.
    - [x] `docker-compose.yml` con servizi per spider, indice e PDF.
    - [x] Volume per persistenza output (`docs_c64/`, `dataset_c64/`) e cache HTTP.
    - [x] Documentazione Docker nel README.
- [x] **Miglioramento Estrazione Codice**:
    - [x] Rilevamento automatico avanzato dei dialetti di assemblaggio (ACME, DASM, Kick Assembler, CA65, Turbo Assembler).
    - [x] Estrazione e tagging di routine e blocchi di codice su tutti gli spider.
    - [x] Modulo `CodeSyntaxValidator` per la verifica formale di opcodes 6502/6510 (inclusi illegal opcodes) e istruzioni BASIC.
- [x] **Integrazione Flusso Continuo con C64-KB-Agent**:
    - [x] Modulo `C64KBNotifier` per generazione di `kb_sync_manifest.json` e notifiche HTTP Webhook.
    - [x] Controllo differenziale (incrementale) basato sul campo `last_modified` / HTTP ETag per tutti gli spider.
- [x] **Integrazione Profonda SDK**:
    - [x] **Feedback Loop**: Supporto scraping on-demand (`main.py scrape-url <URL>`) con auto-detection intelligente dello spider basato sul dominio.
    - [x] **Validazione Automatica**: Verifica sintattica 6502/6510 & BASIC integrata nelle pipeline di output (`docs_c64` frontmatter e `dataset_c64` metadata).
- [x] **CI/CD Pipeline & Secret Management**:
    - [x] GitHub Action "Scrape and Sync" con supporto `--notify-kb` e secret `KB_AGENT_TOKEN` / `KB_WEBHOOK_URL`.
