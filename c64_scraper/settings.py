BOT_NAME = "c64_scraper"

SPIDER_MODULES = ["c64_scraper.spiders"]
NEWSPIDER_MODULE = "c64_scraper.spiders"

# --- Buon comportamento verso il sito (vedi robots.txt di elite.bbcelite.com) ---
ROBOTSTXT_OBEY = True
USER_AGENT = "C64AsmTutorialBot/1.0 (+educational, personal use; contact: your-email@example.com)"

# Delay di base fra le richieste allo stesso dominio
DOWNLOAD_DELAY = 1.5
RANDOMIZE_DOWNLOAD_DELAY = True
CONCURRENT_REQUESTS_PER_DOMAIN = 2
CONCURRENT_REQUESTS = 4

# AutoThrottle adatta dinamicamente la velocità in base al carico/latenza del server,
# invece di forzare un delay fisso: più rispettoso e più efficiente del semplice sleep().
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 1.0
AUTOTHROTTLE_MAX_DELAY = 10.0
AUTOTHROTTLE_TARGET_CONCURRENCY = 1.0
AUTOTHROTTLE_DEBUG = False

# Cache HTTP su disco: se il crawling si interrompe, rilanciando lo spider le pagine
# già scaricate vengono servite dalla cache invece di rifare le richieste di rete.
# Funziona quindi anche come meccanismo di "resume" gratuito.
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 0  # 0 = non scade mai
HTTPCACHE_DIR = "httpcache"
HTTPCACHE_IGNORE_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# Retry automatico su errori temporanei
RETRY_ENABLED = True
RETRY_TIMES = 3

ITEM_PIPELINES = {
    "c64_scraper.pipelines.MarkdownWriterPipeline": 300,
    "c64_scraper.pipelines.JsonDatasetPipeline": 400,
}

# Cartella di output dei file Markdown (sovrascrivibile da riga di comando con -s DOCS_OUTPUT_DIR=...)
DOCS_OUTPUT_DIR = "docs_c64"

# Cartella di output dei file JSONL (sovrascrivibile da riga di comando con -s DATASET_OUTPUT_DIR=...)
DATASET_OUTPUT_DIR = "dataset_c64"

LOG_LEVEL = "INFO"
