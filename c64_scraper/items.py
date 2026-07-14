import scrapy


class DocItem(scrapy.Item):
    """Rappresenta una pagina di documentazione estratta da elite.bbcelite.com."""

    url = scrapy.Field()
    title = scrapy.Field()
    category = scrapy.Field()
    tags = scrapy.Field()
    body_md = scrapy.Field()
    code_blocks = scrapy.Field()  # Lista di dict: {'lang': 'asm', 'code': '...'}
    scraped_at = scrapy.Field()
    last_modified = scrapy.Field()
