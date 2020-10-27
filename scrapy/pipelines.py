# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import logging

from scrapyanon.controllers.DatabaseController import DatabaseController

class ScrapyanonPipeline(object):

    def __init__(self):
        self.db = DatabaseController()

    def process_item(self, item, spider):
        self.db.update_proxy_blocked_status(
            item['ip_address'],
            item['ip_blocked'],
            spider.client_hello,
            spider.name
        )

        return item
