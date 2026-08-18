#!/usr/bin/env python3
import argparse
import os
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

from build_index import build_index
from build_pdf import build_pdf
from build_knowledge_graph import build_knowledge_graph
from build_api_index import build_api_index
from build_search_index import build_search_index
from c64_scraper.utils.kb_notifier import C64KBNotifier

DOMAIN_SPIDER_MAP = {
    "c64-wiki.com": "c64wiki",
    "www.c64-wiki.com": "c64wiki",
    "codebase.c64.org": "codebase64",
    "elite.bbcelite.com": "bbcelite",
    "dustlayer.com": "dustlayer",
    "sta.c64.org": "stac64",
    "archive.org": "archiveorg",
    "github.com": "github",
    "api.github.com": "github"
}

def detect_spider_for_url(url: str, default_spider: str = "c64wiki") -> str:
    parsed = urlparse(url)
    netloc = parsed.netloc.lower()
    for domain, spider_name in DOMAIN_SPIDER_MAP.items():
        if domain in netloc:
            return spider_name
    return default_spider

def run_scrapy(spider, output_dir, extra_args=None):
    print(f"--- Avvio scraping: {spider} ---")
    cmd = ["scrapy", "crawl", spider, "-s", f"DOCS_OUTPUT_DIR={output_dir}"]
    if extra_args:
        cmd.extend(extra_args)
    subprocess.run(cmd, check=True)

def scrape_url(url: str, spider: str, output_dir: str):
    auto_spider = detect_spider_for_url(url, default_spider=spider)
    print(f"--- Scraping singolo URL: {url} (spider rilevato: {auto_spider}) ---")
    cmd = [
        "scrapy", "crawl", auto_spider,
        "-a", f"start_urls={url}",
        "-s", f"DOCS_OUTPUT_DIR={output_dir}",
        "-s", "CLOSESPIDER_PAGECOUNT=1"
    ]
    subprocess.run(cmd, check=True)

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "scrape-url":
        url_parser = argparse.ArgumentParser(description="Scrape a single URL on demand")
        url_parser.add_argument("cmd", choices=["scrape-url"])
        url_parser.add_argument("url", help="URL da scaricare")
        url_parser.add_argument("--spider", default="c64wiki", help="Nome dello spider da usare se non auto-rilevato")
        url_parser.add_argument("--output", default="docs_c64", help="Cartella di output")
        url_parser.add_argument("--notify-kb", action="store_true", help="Genera il manifest di sincronizzazione KB")
        url_parser.add_argument("--webhook-url", help="URL Webhook per notifica a C64-KB-Agent")
        url_args, unknown = url_parser.parse_known_args()

        scrape_url(url_args.url, url_args.spider, url_args.output)

        if url_args.notify_kb or url_args.webhook_url:
            notifier = C64KBNotifier(docs_dir=url_args.output)
            manifest = notifier.generate_manifest(spiders_executed=[url_args.spider])
            webhook_url = url_args.webhook_url or os.getenv("KB_WEBHOOK_URL")
            if webhook_url:
                notifier.send_webhook_notification(webhook_url, manifest, token=os.getenv("KB_AGENT_TOKEN"))
        return

    parser = argparse.ArgumentParser(description="C64 Scraper CLI")
    parser.add_argument("spider", nargs="?", help="Nome dello spider da eseguire (es. bbcelite, codebase64, c64wiki, archiveorg, github, stac64, dustlayer)")
    parser.add_argument("--output", default="docs_c64", help="Cartella di output")
    parser.add_argument("--index", action="store_true", help="Genera l'indice dopo lo scraping")
    parser.add_argument("--pdf", action="store_true", help="Genera il PDF dopo lo scraping")
    parser.add_argument("--all", action="store_true", help="Esegue tutti gli spider definiti")
    parser.add_argument("--incremental", action="store_true", help="Abilita scraping incrementale")
    parser.add_argument("--notify-kb", action="store_true", help="Genera il manifest di sincronizzazione KB")
    parser.add_argument("--webhook-url", help="URL Webhook per notifica a C64-KB-Agent")

    args, unknown = parser.parse_known_args()

    if args.incremental:
        unknown.extend(["-a", "incremental=true"])

    spiders = [args.spider] if args.spider else []
    if args.all:
        spiders = ["bbcelite", "codebase64", "c64wiki", "archiveorg", "github", "stac64", "dustlayer"]

    if not spiders and not (args.index or args.pdf):
        parser.print_help()
        return

    executed = []
    for spider in spiders:
        try:
            run_scrapy(spider, args.output, unknown)
            executed.append(spider)
        except Exception as e:
            print(f"Errore durante lo scraping di {spider}: {e}")

    if args.index or args.all:
        print("--- Generazione Indice ---")
        build_index(Path(args.output))
        print("--- Generazione Knowledge Graph ---")
        build_knowledge_graph(Path(args.output), Path("dataset_c64/knowledge_graph.json"))
        print("--- Generazione API Index ---")
        build_api_index(Path(args.output), Path("dataset_c64/api_index.json"))
        print("--- Generazione SQLite Search Index ---")
        build_search_index(Path(args.output), Path("dataset_c64/search_index.db"))

    if args.pdf:
        print("--- Generazione PDF ---")
        try:
            build_pdf(Path(args.output), Path("manuale_c64.pdf"), "C64 Programming Manual", "C64 Intelligence SDK")
        except Exception as e:
            print(f"Errore generazione PDF: {e}. Assicurati che pandoc sia installato.")

    if args.notify_kb or args.webhook_url or args.all:
        print("--- Generazione Manifest di Sincronizzazione C64-KB-Agent ---")
        notifier = C64KBNotifier(docs_dir=args.output)
        manifest = notifier.generate_manifest(spiders_executed=executed)
        webhook_url = args.webhook_url or os.getenv("KB_WEBHOOK_URL")
        if webhook_url:
            print(f"--- Invio notifica webhook a {webhook_url} ---")
            notifier.send_webhook_notification(webhook_url, manifest, token=os.getenv("KB_AGENT_TOKEN"))

if __name__ == "__main__":
    main()
