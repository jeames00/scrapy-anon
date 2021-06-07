# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy
from itemloaders.processors import TakeFirst

class ProxyExitBlocked(scrapy.Item):
    ip_blocked = scrapy.Field(output_processor=TakeFirst())
    ip_address = scrapy.Field(output_processor=TakeFirst())
    website = scrapy.Field(output_processor=TakeFirst())
