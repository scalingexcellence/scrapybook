# -*- coding: utf-8 -*-

import json
import math
import time

import scrapy
from scrapy.contrib.linkextractors import LinkExtractor
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy import FormRequest
from scrapy.http import Request
from scrapy import log

from twisted.internet import defer
from twisted.internet.task import deferLater
from twisted.internet import reactor

from treq import post

from server import SimpleServer

class DummyItem(scrapy.Item):
    id = scrapy.Field()
    info = scrapy.Field()
    translation = scrapy.Field()

class DummyPipeline(object):
    
    def __init__(self, crawler):
        self.crawler = crawler
        self.blocking_delay = crawler.settings.getfloat('SPEED_PIPELINE_BLOCKING_DELAY', 0.0)
        self.async_delay = crawler.settings.getfloat('SPEED_PIPELINE_ASYNC_DELAY', 0.0)
        self.downloader_api = crawler.settings.getbool('SPEED_PIPELINE_API_VIA_DOWNLOADER', False)
        self.treq_api = crawler.settings.getbool('SPEED_PIPELINE_API_VIA_TREQ', False)
        self.port = crawler.settings.getint('SPEED_PORT', 9312)
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)
    
    @defer.inlineCallbacks
    def process_item(self, item, spider):
        
        # If no processing is made, translation will
        # be N/A
        item['translation'] = "N/A"
        
        if self.blocking_delay > 0.001:
            # This is a bad bad thing
            time.sleep(self.blocking_delay)
        
        if self.async_delay > 0.001:
            # Emulate an asynchronous call to a translation function
            translate = lambda: "calculated-%s" % item['info']
            item['translation'] = yield deferLater(reactor, self.delay, translate)
            
        if self.downloader_api:
            # Do an API call using Scrapy's downloader
            request = FormRequest("http://192.168.1.9:%d/api" % self.port, formdata=dict(text=item['info']))
            response = yield self.crawler.engine.download(request, spider)
            item['translation'] = json.loads(response.body)['translation']

        if self.treq_api:
            # Do an API call using treq
            response = yield post("http://192.168.1.9:%d/api" % self.port, {"text":item['info']})
            json_response = yield response.json()
            item['translation'] = json_response['translation']
        
        defer.returnValue(item)
        
class SpeedSpider(CrawlSpider):
    name = 'speed'

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        return cls(crawler, *args, **kwargs)
    
    def __init__(self, crawler, *args, **kwargs):
        super(SpeedSpider, self).__init__(*args, **kwargs)
        
        if not crawler.settings.getbool('SPEED_SKIP_SERVER', False):
            port = crawler.settings.getint('SPEED_PORT', 9312)
            self.server = SimpleServer(port, crawler.settings)
                
    def get_detail_requests(self):
        port = self.settings.getint('SPEED_PORT', 9312)
        items_per_page = self.settings.getint('SPEED_ITEMS_PER_DETAIL', 1)
        total_items = self.settings.getint('SPEED_TOTAL_ITEMS', 1000)
        return [Request('http://localhost:%d/detail?id0=%d' % (port, i), callback=self.parse_item) for i in xrange(1, total_items+1, items_per_page)]
                
    def start_requests(self):
        start_requests_style = self.settings.get('SPEED_START_REQUESTS_STYLE', 'Force')
        
        if start_requests_style == 'UseIndex':
            # The requests out of the index page get processed in the same
            # parallel(... CONCURRENT_ITEMS) among regular Items.
            yield self.make_requests_from_url('http://localhost:%d/index' % self.port)
        elif start_requests_style == 'Force':
            # This is feeding those requests directly into the scheduler's
            # queue.
            for request in self.get_detail_requests():
                self.crawler.engine.crawl(request=request, spider=self)
        elif start_requests_style == 'Iterate':
            # start_requests are consumed "on demand" through yield
            for request in self.get_detail_requests():
                yield request        
        else:
            print "No start_requests."
    
    def closed(self, reason):
        if hasattr(self,'server'):
            self.server.close()

    def my_process_request(self, r):
        if self.settings.getbool('SPEED_INDEX_HIGHER_PRIORITY', True):
            r.priority = 1
        return r

    rules = (
        Rule(LinkExtractor(restrict_xpaths='//*[@class="nav"]'), process_request="my_process_request"),
        Rule(LinkExtractor(restrict_xpaths='//*[@class="item"]'), callback='parse_item')
    ) 

    def parse_item(self, response):
        
        for li in response.xpath('//li'):
            i = DummyItem()
            id_phrase = li.xpath('.//h3/text()').extract()[0]
            i['id'] = int(id_phrase.split()[1])
            i['info'] = li.xpath('.//div[@class="info"]/text()').extract()
            yield i