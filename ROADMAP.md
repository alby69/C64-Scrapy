# Roadmap - C64 Scraper

Questo documento delinea l'evoluzione del modulo Scraper all'interno dell'ecosistema C64 Intelligence SDK.

## Obiettivi a Breve Termine

- [ ] **Nuovi Spider**:
    - [ ] `c64wiki`: Estrazione sistematica da [C64-Wiki](https://www.c64-wiki.com/).
    - [ ] `lemon64`: Crawling dei forum tecnici e documentazione.
    - [ ] `archive_org`: Download automatizzato di manuali PDF e conversione in testo.
- [ ] **Miglioramento Estrazione Codice**:
    - [ ] Integrazione con `c64extractor` (shared package SDK) per il disassemblaggio automatico dei blocchi di dati trovati nelle pagine.
    - [ ] Rilevamento automatico della sintassi (ACME, DASM, KickAssembler).

## Obiettivi a Medio Termine

- [ ] **AI-Powered Scraping**:
    - [ ] Pipeline di post-processing che utilizza un LLM locale per riassumere i documenti lunghi durante lo scraping.
    - [ ] Generazione automatica di coppie Q&A (Domanda/Risposta) per il fine-tuning direttamente in fase di crawling.
- [ ] **Dashboard di Monitoraggio**:
    - [ ] Semplice interfaccia web per monitorare lo stato dei crawl e la qualità della Knowledge Base prodotta.

## Integrazione Profonda SDK

- [ ] **Feedback Loop**: Permettere agli agenti di `C64-LLM` di richiedere lo scraping di un URL specifico se non trovano informazioni nella KB locale.
- [ ] **Validazione Automatica**: Passare ogni snippet di codice estratto al modulo `c64validator` per verificarne la correttezza prima di inserirlo nella KB.
