import json
import time
import scrapy
from scrapy import signals
from c64_scraper.items import DocItem
from c64_scraper.utils.incremental_manager import IncrementalStateManager
from c64_scraper.utils.reporter import RunReporter

class GithubSpider(scrapy.Spider):
    name = "github"
    allowed_domains = ["github.com", "api.github.com"]
    start_urls = [
        "https://api.github.com/search/repositories?q=commodore-64+language:assembly",
        "https://api.github.com/search/repositories?q=c64+6502"
    ]

    def __init__(self, incremental: str = "false", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.incremental = str(incremental).lower() in ("true", "1", "yes")
        self.state_manager = IncrementalStateManager()
        self.reporter = RunReporter()

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_closed(self, spider):
        self.state_manager.save_state(self.name)
        self.reporter.generate_report(self.name)
        self.logger.info("Saved incremental state and generated run report.")

    def parse(self, response):
        try:
            data = json.loads(response.text)
        except Exception as e:
            self.logger.error("Failed to parse JSON response from GitHub API")
            self.reporter.record_error(response.url, str(e))
            return

        items = data.get("items", [])
        for repo in items:
            repo_name = repo.get("full_name")
            repo_url = repo.get("html_url")
            description = repo.get("description") or "No description provided."
            stars = repo.get("stargazers_count", 0)
            pushed_at = repo.get("pushed_at")

            if self.incremental and pushed_at:
                if self.state_manager.is_page_unmodified(self.name, repo_url, pushed_at):
                    self.logger.info(f"Skipping unmodified repository: {repo_url}")
                    self.reporter.record_skipped(repo_url)
                    continue

            item = DocItem()
            item["url"] = repo_url
            item["title"] = f"GitHub Repo: {repo_name}"
            item["category"] = "github"
            item["tags"] = ["c64", "assembly", "github", "source-code"]

            body_md = f"## {repo_name}\n\n"
            body_md += f"**Description:** {description}\n\n"
            body_md += f"**GitHub URL:** {repo_url}\n"
            body_md += f"**Stars:** {stars}\n"
            body_md += f"**Last Updated:** {pushed_at}\n"

            item["body_md"] = body_md
            item["code_blocks"] = []
            item["scraped_at"] = time.strftime("%Y-%m-%d")
            if pushed_at:
                item["last_modified"] = pushed_at

            self.state_manager.update_page_state(self.name, repo_url, pushed_at, item["scraped_at"])
            self.reporter.record_scraped(repo_url)

            yield item
