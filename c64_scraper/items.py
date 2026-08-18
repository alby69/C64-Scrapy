import scrapy


class DocItem(scrapy.Item):
    """Rappresenta una pagina di documentazione estratta da uno dei siti supportati."""

    url = scrapy.Field()
    title = scrapy.Field()
    category = scrapy.Field()
    tags = scrapy.Field()
    body_md = scrapy.Field()
    code_blocks = scrapy.Field()  # Lista di dict: {'lang': 'asm', 'code': '...'}
    scraped_at = scrapy.Field()
    last_modified = scrapy.Field()
    license = scrapy.Field()
    wiki_revision_id = scrapy.Field()
    topics = scrapy.Field()
    difficulty = scrapy.Field()
    language = scrapy.Field()
    hardware = scrapy.Field()
    related = scrapy.Field()
