# Roadmap - C64 Scraper

Questo documento delinea l'evoluzione del modulo Scraper all'interno dell'ecosistema C64 Intelligence SDK.

## Filosofia Decoupled

In accordo con l'architettura generale dell'SDK, il modulo **C64-Scrapy** si limita a compiti di:
- **Scraping ed estrazione di dati puliti** dal web (siti di riferimento, libri, tutorial, forum).
- **Conversione dei contenuti in Markdown standard** con frontmatter YAML.
- **Rilevamento e isolamento dei blocchi di codice** (Assembly 6502 e BASIC).
- **Generazione di record JSONL deterministici** dotati di ID SHA256 univoco basato sull'URL della risorsa.

Tutti i compiti di **strutturazione avanzata, memorizzazione vettoriale, chunking, deduplicazione e controllo di consistenza** sono delegati all'agente centralizzato **[C64-KB-Agent](https://github.com/alby69/C64-KB-Agent)**.

---

## Obiettivi a Breve Termine

- [x] **Nuovi Spider**:
    - [x] `c64wiki`: Estrazione sistematica da [C64-Wiki](https://www.c64-wiki.com/).
    - [x] `codebase64`: Corretto dominio e start url su `https://codebase.c64.org/`.
    - [x] `archiveorg`: Estrazione di metadati e testi da Archive.org.
    - [x] `github`: Ricerca automatica di repository con assembly C64.
- [x] **Docker & Containerizzazione**:
    - [x] `Dockerfile` multi-stage con Python, pandoc e texlive.
    - [x] `docker-compose.yml` con servizi per spider, indice e PDF.
    - [x] Volume per persistenza output (`docs_c64/`, `dataset_c64/`) e cache HTTP.
    - [x] Documentazione Docker nel README.
- [ ] **Miglioramento Estrazione Codice**:
    - [ ] Affinare il rilevamento automatico della sintassi (ACME, DASM, KickAssembler).
    - [ ] Migliorare l'estrazione dei blocchi di codice per gli altri spider.

## Obiettivi a Medio Termine

- [ ] **Integrazione Flusso Continuo con C64-KB-Agent**:
    - [ ] Creazione di script/webhook di push per notificare `C64-KB-Agent` non appena nuovi documenti vengono scaricati o aggiornati.
    - [ ] Implementazione di un controllo differenziale (incrementale) basato sul campo `last_modified` per non riscaricare pagine non modificate.

## Integrazione Profonda SDK

- [ ] **Feedback Loop**: Permettere agli agenti di `C64-LLM` di richiedere a `C64-KB-Agent` lo scraping on-demand di un URL specifico, che a sua volta invoca questo Scraper.
- [ ] **Validazione Automatica**: Passare ogni snippet di codice estratto al modulo di validazione sintattica dell'SDK per verificarne la correttezza formale.

## Integrazione Profonda SDK

- [ ] **Feedback Loop**: Permettere agli agenti di `C64-LLM` di richiedere a `C64-KB-Agent` lo scraping on-demand di un URL specifico, che a sua volta invoca questo Scraper.
- [ ] **Validazione Automatica**: Passare ogni snippet di codice estratto al modulo di validazione sintattica dell'SDK per verificarne la correttezza formale.

## CI/CD Pipeline

- [x] **GitHub Action "Scrape and Sync"**:
    - [x] Trigger manuale (`workflow_dispatch`) con selezione spider
    - [x] Cron settimanale (lunedì 06:00 UTC)
    - [x] Setup Python + pandoc + dipendenze
    - [x] Esecuzione spider + generazione indici
    - [x] Push automatico a `C64-KB-Agent/data/`
- [ ] **Secret Management**:
    - [ ] Configurare `KB_AGENT_TOKEN` (PAT con scope `repo`)
