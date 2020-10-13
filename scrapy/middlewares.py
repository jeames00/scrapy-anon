# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

import os, logging, asyncio

import concurrent.futures
from scrapy import signals
from scrapy.http import HtmlResponse
from twisted.internet import threads, defer
#from twisted.internet.defer import Deferred, ensureDeferred

import grpc, http_pb2, http_pb2_grpc
from grpc import aio

class ScrapyanonSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class ScrapyanonDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    def __init__(self, useragent):
        self.useragent = useragent

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        useragent = crawler.settings.get('USER_AGENT')
        s = cls(useragent)
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(s.spider_closed, signal=signals.spider_closed)
        return s 



    def fetch_url(self, kwargs):
        print("** fetch_url **")
        async def fetching(kwargs):
            self.http_host_port = os.environ['HTTP_GRPC_PORT']
            self.headers = kwargs["headers"]
            self.proxy = kwargs["proxy"]
            self.hostName = kwargs["hostName"]
            self.domainName = kwargs["domainName"]
            self.url = kwargs["url"]
            self.spider = kwargs["spider"]
            self.clientHello = kwargs["clientHello"]

         #   channel = Channel(port = self.http2_server_port)
         #   server_stub = HttpClientStub(channel)

            channel = aio.insecure_channel('http:'+self.http_host_port)
            await channel.channel_ready()
            stub = http_pb2_grpc.HttpClientStub(channel)
            reply = await stub.GetURL(
                http_pb2.Request(
            
      #  reply: Response = await server_stub.GetURL(Request(
                    url=self.url,
                    scrapySpider=self.spider,
                    domainName=self.domainName,
                    host=self.hostName,
                    proxy=self.proxy,
                    headers=self.headers,
                    clientHello=self.clientHello))

            await channel.close()
            if reply.error == "":
                return (reply.status,
                        reply.headers, 
                        reply.body)
            else:
                return reply.error

        return asyncio.run(fetching(kwargs))

    @defer.inlineCallbacks
    def process_request(self, request, spider):
        print("** process_request **")
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called

        kwargs = {
            'url':          request.url,
            'headers':      request.headers,
            'spider':       spider.name,
            'domainName':   request.meta['domain_name'],
            'hostName':     request.meta['host_name'],
            'proxy':        request.meta['proxy'],
            'clientHello':  request.meta['client_hello']
        }


        if 'alt-svc' in request.meta:
            kwargs['alt-svc'] = request.meta['alt-svc']

        response = yield threads.deferToThread(self.fetch_url, kwargs)

        if isinstance(response, tuple):
            return HtmlResponse(url = request.url,
                                status = int(response[0].split(' ')[0]),
                                headers = response[1],
                                body = response[2],
                                request = request,
                                encoding = 'utf-8')
        else:
            return HtmlResponse(url = request.url,
                                body = response,
                                request = request,
                                encoding = 'utf-8')

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
   #     self.executor = concurrent.futures.ThreadPoolExecutor(10)

    def spider_closed(self, spider):
        print("closing spider")
