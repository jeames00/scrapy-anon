# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html

import os, logging, asyncio, sys

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
            self.method = kwargs["method"]
            self.body = kwargs["body"]
            self.proxy = kwargs["proxy"]
            self.url = kwargs["url"]
            self.clientHello = kwargs["clientHello"]
            self.httpClientID = kwargs["httpClientID"]

            channel = aio.insecure_channel('http:'+self.http_host_port)
            await channel.channel_ready()
            stub = http_pb2_grpc.HttpClientStub(channel)
            reply = await stub.GetURL(
                http_pb2.Request(
                    url=self.url,
                    proxy=self.proxy,
                    headers=self.headers,
                    method=self.method,
                    body=self.body,
                    clientHello=self.clientHello,
                    httpClientID=self.httpClientID))

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

        # Proxy for http-fetcher is empty (i.e. nil) by default unless
        # passed in request
        http_fetcher_args = {
            'url':  request.url,
            'headers': request.headers
        }

        # If client_hello isn't passed, exit the function to let scrapy
        # process the request
        try:
            http_fetcher_args['clientHello'] = request.meta['client_hello']
        except KeyError:
            return None

        # httpClientID is used to identify which cached roundTripper to (re)use
        # in http-fetcher
        try:
            http_fetcher_args['httpClientID'] = request.meta['http_client_id']
        except KeyError:
            return None

        # Set the proxy for http-fetcher if it's passed in request
        try:
            http_fetcher_args['proxy'] = request.meta['proxy']
        except KeyError:
            http_fetcher_args['proxy'] = ""

        # Body to be passed to http_fetcher
        try:
            http_fetcher_args['body'] = request.body.decode("UTF-8")
        except AttributeError:
            pass

        # Request method to be passed to http_fetcher
        try:
            http_fetcher_args['method'] = request.method
        except AttributeError:
            pass

        # pass the 'alt-svc' host address if provided
        try:
            http_fetcher_args['alt-svc'] = request.meta['alt-svc']
        except KeyError:
            pass

        response = yield threads.deferToThread(self.fetch_url, http_fetcher_args)

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
