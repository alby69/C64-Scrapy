import scrapy
import json
import time
from c64_scraper.items import DocItem
from c64_scraper.utils.processor import ContentProcessor

class GithubSpider(scrapy.Spider):
    name = "github"
    allowed_domains = ["github.com", "api.github.com"]
    start_urls = [
        "https://api.github.com/search/repositories?q=commodore-64+language:assembly",
        "https://api.github.com/search/repositories?q=c64+6502"
    ]

    def parse(self, response):
        try:
            data = json.loads(response.text)
        except Exception:
            self.logger.error("Failed to parse JSON response from GitHub API")
            return

        items = data.get("items", [])
        for repo in items:
            repo_name = repo.get("full_name")
            repo_url = repo.get("html_url")
            description = repo.get("description") or "No description provided."
            stars = repo.get("stargazers_count", 0)
            pushed_at = repo.get("pushed_at")

            # Create a structured document item for the repository metadata
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

            yield item
