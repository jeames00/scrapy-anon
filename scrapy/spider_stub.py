import scrapy, json
from scrapy.spidermiddlewares.httperror import HttpError
from scrapy.loader import ItemLoader
from itemloaders.processors import TakeFirst
from scrapy.exceptions import NotConfigured

class TorExitBlocked(scrapy.Item):
    ip_blocked = scrapy.Field(output_processor=TakeFirst())
    ip_address = scrapy.Field(output_processor=TakeFirst())
    host_name = scrapy.Field(output_processor=TakeFirst())
    response_text = scrapy.Field(output_processor=TakeFirst())
    response_status = scrapy.Field(output_processor=TakeFirst())

class StubSpider(scrapy.Spider):

    def __init__(self, **kwargs):
        self.pc = ProxyController()
        self.proxies = self.pc.get_proxies(
            len(self.urls), 
            spider=QuotesSpider.name
        )
        self.domain_name = "**DOMAIN NAME**"
        self.host_name = "**HOST NAME**"
        self.client_hello = kwargs['client_hello']
        self.headers = json.loads(kwargs['client_hello'])['headers']
        for k in self.headers:
            self.headers[k] = self.headers[k][0]

    name = "_stub"

    urls = [
        "**URL**",
    ] 

    def start_requests(self):
        headers = json.loads(self.client_hello)['headers']
        for k in headers:
            headers[k] = headers[k][0]

        for url in self.urls:
            yield scrapy.Request(
                url=url,
                callback=self.parse,
                errback=self.errback,
                headers=headers,
                meta = {
           #         "cookiejar": i,
                    "domain_name": self.domain_name,
                    "host_name": self.host_name,
                    "proxy": self.proxies[i][0],
                    "exit_ip_address": self.proxies[i][1],
                    "client_hello": self.client_hello
                },
            )

    def parse(self, response):
        l = ItemLoader(item = TorExitBlocked(), response = response)
    #   custom code to check if request was denied by server
    #   if xxxxx:
    #       l.add_value('ip_blocked', False)
    #   else:
    #       l.add_value('ip_blocked', True)
        l.add_value('ip_address', response.request.meta['exit_ip_address'])
        l.add_value('host_name', response.request.meta['host_name'])
        l.add_value('response_text', response.text)
        l.add_value('response_status', response.status)
        yield l.load_item()

    def errback(self, failure):
        self.logger.error(repr(failure))

        if failure.check(HttpError):
            response = failure.value.response
            self.logger.error('HttpError on %s', response.url)
            l = ItemLoader(item = TorExitBlocked(), response = response)
            l.add_value('ip_blocked', True)
            l.add_value('ip_address', response.request.meta['exit_ip_address'])
            l.add_value('host_name', response.request.meta['host_name'])
            l.add_value('response_text', response.text)
            l.add_value('response_status', response.status)
            yield l.load_item()

