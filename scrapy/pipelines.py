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
        self.db.upsert_rows(
                rows = [{ 
                    'website': item['website'],
                    'blocked': item['ip_blocked']
                }],
                table_name = 'ClientHelloProxy',
                constraint = 'website_proxy_id_constraint',
                foreign_keys = [
                    {'foreign_key': 'proxy_id',
                    'parent_table': 'Proxy',
                    'parent_column': 'ip_address',
                    'column_value': item['ip_address']},

                    {'foreign_key': 'client_hello_id',
                    'parent_table': 'ClientHello',
                    'parent_column': 'client_hello',
                    'column_value': spider.client_hello}
               ]
        )

        return item
