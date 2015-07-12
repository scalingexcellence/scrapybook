# -*- coding: utf-8 -*-

import json
import time

from treq import post

from twisted.internet import defer
from twisted.internet.task import deferLater
from twisted.internet import reactor

import scrapy

from scrapy import FormRequest
from scrapy.http import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from server import SimpleServer


class DummyItem(scrapy.Item):
    id = scrapy.Field()
    info = scrapy.Field()
    translation = scrapy.Field()


class DummyPipeline(object):

    def __init__(self, crawler):
        self.crawler = crawler
        self.blocking_delay = crawler.settings.getfloat(
            'SPEED_PIPELINE_BLOCKING_DELAY', 0.0)
        self.async_delay = crawler.settings.getfloat(
            'SPEED_PIPELINE_ASYNC_DELAY', 0.0)
        self.downloader_api = crawler.settings.getbool(
            'SPEED_PIPELINE_API_VIA_DOWNLOADER', False)
        self.treq_api = crawler.settings.getbool(
            'SPEED_PIPELINE_API_VIA_TREQ', False)
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
            translation = yield deferLater(reactor, self.delay, translate)
            item['translation'] = translation

        if self.downloader_api:
            # Do an API call using Scrapy's downloader
            url = "http://192.168.1.9:%d/api"
            formdata = dict(text=item['info'])
            request = FormRequest(url % self.port, formdata=formdata)
            response = yield self.crawler.engine.download(request, spider)
            item['translation'] = json.loads(response.body)['translation']

        if self.treq_api:
            # Do an API call using treq
            url = "http://192.168.1.9:%d/api"
            response = yield post(url % self.port, {"text": item['info']})
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

        callback = self.parse_item
        url = 'http://localhost:%d/detail?id0=%d'
        m_range = xrange(1, total_items+1, items_per_page)
        return [Request(url % (port, i), callback=callback) for i in m_range]

    def start_requests(self):
        start_requests_style = self.settings.get('SPEED_START_REQUESTS_STYLE',
                                                 'Force')

        if start_requests_style == 'UseIndex':
            # The requests out of the index page get processed in the same
            # parallel(... CONCURRENT_ITEMS) among regular Items.
            url = 'http://localhost:%d/index' % self.port
            yield self.make_requests_from_url(url)
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
        if hasattr(self, 'server'):
            self.server.close()

    def my_process_request(self, r):
        if self.settings.getbool('SPEED_INDEX_HIGHER_PRIORITY', True):
            r.priority = 1
        return r

    rules = (
        Rule(LinkExtractor(restrict_xpaths='//*[@class="nav"]'),
             process_request="my_process_request"),
        Rule(LinkExtractor(restrict_xpaths='//*[@class="item"]'),
             callback='parse_item')
    )

    def parse_item(self, response):

        for li in response.xpath('//li'):
            i = DummyItem()
            id_phrase = li.xpath('.//h3/text()').extract()[0]
            i['id'] = int(id_phrase.split()[1])
            i['info'] = li.xpath('.//div[@class="info"]/text()').extract()
            yield i
