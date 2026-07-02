# Specifiche tecniche (v2, Scrapy) — Estrazione documentazione elite.bbcelite.com per tutorial ASM C64

## 1. Obiettivo

Le stesse finalità della v1 (cartella Markdown organizzata + `index.md`, manuale PDF unico,
possibile integrazione come Knowledge Base RAG nel progetto
[alby69/C64-LLM](https://github.com/alby69/C64-LLM)), ma con lo scraping riscritto usando il
framework **Scrapy** invece di `requests` "a mano": crawling asincrono, rispetto nativo di
`robots.txt`, throttling adattivo, cache HTTP per il resume, retry automatici.

## 2. Nota legale / etica (invariata)

Il sito è *"provided on an educational and non-profit basis"*, copyright di Mark Moxon /
Ian Bell / David Braben. Per un progetto didattico personale va bene, rispettando:
`robots.txt`, un ritmo di richieste contenuto, l'attribuzione della fonte in ogni file, nessuna
redistribuzione commerciale. Tutti questi vincoli sono implementati nelle `settings.py` dello
spider (vedi §4.3).

## 3. Perché Scrapy invece di requests+BeautifulSoup

| Aspetto              | v1 (requests)                         | v2 (Scrapy)                                                  |
|-----------------------|----------------------------------------|----------------------------------------------------------------|
| Crawling              | loop manuale BFS con `deque`           | motore asincrono nativo (Twisted), scheduler + duplicate filter |
| robots.txt            | parsing manuale con `urllib.robotparser` | `ROBOTSTXT_OBEY = True`, gestito dal framework                |
| Rate limiting         | `time.sleep(delay)` fisso              | `AUTOTHROTTLE` adattivo in base alla latenza del server         |
| Resume dopo interruzione | da reimplementare (stato URL visitati) | `HTTPCACHE_ENABLED` — le pagine già scaricate non vengono rifatte |
| Retry su errori 5xx/429 | da reimplementare                     | `RETRY_ENABLED` + `RETRY_TIMES` integrati                       |
| Estrazione link        | BeautifulSoup + filtri manuali         | `LinkExtractor` con regex di allow/deny dichiarative            |
| Estensibilità          | funzioni sparse                        | architettura a componenti: Spider / Item / Pipeline / Settings  |

## 4. Struttura del progetto Scrapy

```
bbcelite_scraper/
├── scrapy.cfg
├── requirements.txt
├── build_index.py              # invariato rispetto alla v1: post-processing
├── build_pdf.py                # invariato rispetto alla v1: post-processing
└── bbcelite_scraper/
    ├── __init__.py
    ├── items.py                 # DocItem: url, title, category, tags, body_md, scraped_at
    ├── pipelines.py              # MarkdownWriterPipeline: item -> file .md con frontmatter
    ├── settings.py                # robots.txt, throttling, cache, pipeline registrata
    └── spiders/
        ├── __init__.py
        └── bbcelite.py            # CrawlSpider con le regole di navigazione
```

### 4.1 `items.py`

Definisce il contratto dati (`DocItem`) fra spider e pipeline: `url`, `title`, `category`,
`tags`, `body_md` (già in Markdown), `scraped_at`. Usare un `Item` esplicito invece di un dict
generico dà validazione della struttura e rende il progetto estendibile (es. aggiungere in
futuro `code_blocks` per gli snippet assembly).

### 4.2 `spiders/bbcelite.py`

Un `CrawlSpider` (non uno `Spider` semplice) perché il sito va **navigato seguendo i link**
delle pagine indice, non scaricato da una lista fissa di URL. Le `Rule` con `LinkExtractor`
limitano il crawling ai soli path richiesti (`about_site/`, `deep_dives/`, `c64/indexes/`,
`hacks/`, personalizzabili con `-a sections=...`), così lo spider non finisce a scaricare le
versioni BBC Micro/Apple II/NES o le pagine di licenza non pertinenti al tutorial C64.

Per ogni pagina (`parse_item`), l'estrazione del contenuto principale (senza nav/menu/footer)
usa **`trafilatura`**, la stessa scelta della v1: è agnostico rispetto ai nomi delle classi CSS
del sito e produce già Markdown pulito.

### 4.3 `settings.py` — comportamento responsabile

```python
ROBOTSTXT_OBEY = True
DOWNLOAD_DELAY = 1.5
AUTOTHROTTLE_ENABLED = True          # adatta il ritmo alla risposta reale del server
HTTPCACHE_ENABLED = True             # cache su disco = resume gratuito dopo un'interruzione
RETRY_ENABLED = True
```

### 4.4 `pipelines.py`

`MarkdownWriterPipeline` riceve ogni `DocItem` già estratto dallo spider e lo scrive su disco
come file `.md` con frontmatter YAML, rispecchiando la struttura di path del sito
(`/deep_dives/maths/foo.html` → `deep_dives/maths/foo.md`), esattamente come nella v1.

## 5. Esecuzione

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt        # scrapy, trafilatura, pyyaml, pypandoc

cd bbcelite_scraper

# 1. Scraping (asincrono, con throttling adattivo e cache automatica)
scrapy crawl bbcelite \
    -a sections="about_site,deep_dives,c64/indexes,hacks" \
    -s DOCS_OUTPUT_DIR=../docs_bbcelite

# 2. Costruzione indice di navigazione (identico alla v1)
python ../build_index.py --docs ../docs_bbcelite   # eseguito da dentro bbcelite_scraper/
# oppure, se lanciato dalla root del progetto:
python build_index.py --docs docs_bbcelite

# 3. Generazione del manuale PDF (identico alla v1)
python build_pdf.py --docs docs_bbcelite --out manuale_c64_elite.pdf \
    --title "Elite 6502: Manuale di programmazione Assembly per Commodore 64" \
    --author "Estratto da elite.bbcelite.com (Mark Moxon) — raccolta a cura personale"
```

Se il crawling si interrompe (Ctrl+C, timeout, errore di rete), rilanciando lo stesso comando
`scrapy crawl bbcelite ...` le pagine già presenti in `httpcache/` vengono servite dalla cache
locale invece di essere riscaricate: il crawl riparte "quasi da dove si era interrotto" senza
codice aggiuntivo.

Per debug puntuale su una singola pagina, utile durante lo sviluppo:

```bash
scrapy parse --spider=bbcelite -c parse_item \
    "https://elite.bbcelite.com/deep_dives/sound_effects_in_commodore_64_elite.html"
```

## 6. Output e formato file (invariati rispetto alla v1)

```
docs_bbcelite/
├── index.md
├── about_site/...
├── deep_dives/
│   ├── maths/...
│   ├── sound_and_music/sound_effects_in_commodore_64_elite.md
│   └── ...
├── c64/indexes/...
└── hacks/...
```

Ogni file:

```yaml
---
title: "Sound effects in Commodore 64 Elite"
source_url: "https://elite.bbcelite.com/deep_dives/sound_effects_in_commodore_64_elite.html"
category: "deep_dives"
tags: [c64, sid]
scraped_at: "2026-07-02"
---
```

## 7. Integrazione con C64-LLM (RAG) — invariata

Il repo `alby69/C64-LLM` ha una `knowledge_base/` indicizzata con FAISS da
`agent/knowledge_base.py`, che accetta `.md` con frontmatter `title`+`tags` — lo stesso formato
prodotto da `MarkdownWriterPipeline`. Basta quindi:

```bash
cp -r docs_bbcelite/* /path/to/C64-LLM/knowledge_base/bbcelite/
cd /path/to/C64-LLM
docker compose run --rm c64-pipeline python agent/knowledge_base.py
docker compose restart c64-ui
```

In alternativa, per un'integrazione più "nativa", si può copiare l'intera cartella
`bbcelite_scraper/` dentro `C64-LLM/pipeline/` come nuovo spider Scrapy accanto a
`c64_asm_scraper.py`, così il progetto ha un'unica pipeline di scraping per tutte le fonti
(6502.org, codebase64, c64wiki, bbcelite) con lo stesso stile di configurazione.

## 8. Estensioni possibili

- **`FEEDS`** di Scrapy per esportare in parallelo anche un JSON/CSV con i metadati di tutte le
  pagine (utile come "manifest" per la knowledge base), es.:
  `-o docs_bbcelite/_manifest.jsonl:jsonlines`.
- Uno `spider_middleware` per estrarre separatamente i blocchi di codice assembly (```asm```)
  in un campo `code_blocks` del `DocItem`, utile sia al tutorial sia a un futuro fine-tuning.
- `scrapy crawl bbcelite -s JOBDIR=crawls/bbcelite-1` per una persistenza dello stato dello
  scheduler ancora più robusta della sola cache HTTP (pausa/riprendi esplicito del crawl).
- Export anche in EPUB (`pandoc -o manuale.epub`) riusando `build_pdf.py` come base.
