# -*- coding: utf-8 -*-

import json
import time

from treq import post

from twisted.internet.task import deferLater
from twisted.internet import defer, reactor, task

import scrapy

from scrapy import FormRequest
from scrapy.http import Request
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy.exceptions import NotConfigured
from scrapy import signals


settings_to_url = {
    # Website structure
    "SPEED_TOTAL_ITEMS": "ti",
    "SPEED_DETAILS_PER_INDEX_PAGE": "dp",
    "SPEED_ITEMS_PER_DETAIL": "id",
    "SPEED_DETAIL_EXTRA_SIZE": "ds",
    "SPEED_INDEX_POINTAHEAD": "ip",
    # Response times
    "SPEED_T_RESPONSE": "rr",
    "SPEED_API_T_RESPONSE": "ar",
    "SPEED_DETAIL_T_RESPONSE": "dr",
    "SPEED_INDEX_T_RESPONSE": "ir",
}


def get_base_url(settings):
    port = settings.getint('SPEED_PORT', 9312)
    args = []
    for (setting, arg_name) in settings_to_url.iteritems():
        arg_value = settings.get(setting)
        # If a setting is set, then reflect that to the URL
        if arg_value:
            args.append("/%s:%s" % (arg_name, arg_value))

    return "http://web:%d%s/benchmark/" % (port, "".join(args))


class DummyItem(scrapy.Item):
    id = scrapy.Field()
    info = scrapy.Field()
    translation = scrapy.Field()


class SpeedSpider(CrawlSpider):
    name = 'speed'

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        if crawler.settings.getbool('SPEED_INDEX_RULE_LAST', False):
            cls.rules = (cls.rules[1], cls.rules[0])

        spider = super(SpeedSpider, cls).from_crawler(crawler, *args, **kwargs)

        spider.blocking_delay = crawler.settings.getfloat(
            'SPEED_SPIDER_BLOCKING_DELAY', 0.0)
        spider.base = get_base_url(crawler.settings)

        return spider

    def get_detail_requests(self):
        items_per_page = self.settings.getint('SPEED_ITEMS_PER_DETAIL', 1)
        total_items = self.settings.getint('SPEED_TOTAL_ITEMS', 1000)

        for i in xrange(1, total_items+1, items_per_page):
            yield Request(self.base + "detail?id0=%d" % i,
                          callback=self.parse_item)

    def start_requests(self):
        start_requests_style = self.settings.get('SPEED_START_REQUESTS_STYLE',
                                                 'Force')

        if start_requests_style == 'UseIndex':
            # The requests out of the index page get processed in the same
            # parallel(... CONCURRENT_ITEMS) among regular Items.
            index_shards = self.settings.getint('SPEED_INDEX_SHARDS', 1)

            index_pages_count = self.get_index_pages_count()

            # Round up
            shard_length = (index_pages_count+index_shards-1) / index_shards

            for i in xrange(1, index_pages_count, shard_length):
                url = self.base + "index?p=%d" % i
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

    def get_index_pages_count(self):
        details_per_index = self.settings.getint(
            'SPEED_DETAILS_PER_INDEX_PAGE', 20)
        items_per_page = self.settings.getint('SPEED_ITEMS_PER_DETAIL', 1)

        page_worth = details_per_index * items_per_page

        total_items = self.settings.getint('SPEED_TOTAL_ITEMS', 1000)

        # Round up
        index_pages_count = (total_items + page_worth - 1) / page_worth

        return index_pages_count

    def my_process_request(self, r):
        if self.settings.getbool('SPEED_INDEX_HIGHER_PRIORITY', False):
            r.priority = 1
        return r

    rules = (
        Rule(LinkExtractor(restrict_xpaths='//*[@class="nav"]'),
             process_request="my_process_request"),
        Rule(LinkExtractor(restrict_xpaths='//*[@class="item"]'),
             callback='parse_item')
    )

    def parse_item(self, response):
        if self.blocking_delay > 0.001:
            # This is a bad bad thing
            time.sleep(self.blocking_delay)

        for li in response.xpath('//li'):
            i = DummyItem()
            id_phrase = li.xpath('.//h3/text()').extract()[0]
            i['id'] = int(id_phrase.split()[1])
            i['info'] = li.xpath('.//div[@class="info"]/text()').extract()
            yield i


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
        self.base = get_base_url(crawler.settings)

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
            delay = self.async_delay
            translate = lambda: "calculated-%s" % item['info']
            translation = yield deferLater(reactor, delay, translate)
            item['translation'] = translation

        if self.downloader_api:
            # Do an API call using Scrapy's downloader
            formdata = dict(text=item['info'])
            request = FormRequest(self.base + "api", formdata=formdata)
            response = yield self.crawler.engine.download(request, spider)
            item['translation'] = json.loads(response.body)['translation']

        if self.treq_api:
            # Do an API call using treq
            response = yield post(self.base + "api", {"text": item['info']})
            json_response = yield response.json()
            item['translation'] = json_response['translation']

        defer.returnValue(item)


class PrintCoreMetrics(object):
    """
    An extension that prints "core metrics"
    """
    @classmethod
    def from_crawler(cls, crawler):
        return cls(crawler)

    def __init__(self, crawler):
        self.crawler = crawler
        self.interval = crawler.settings.getfloat('CORE_METRICS_INTERVAL', 1.0)
        self.first = True

        if not self.interval:
            raise NotConfigured

        cs = crawler.signals
        cs.connect(self._spider_opened, signal=signals.spider_opened)
        cs.connect(self._spider_closed, signal=signals.spider_closed)

    def _spider_opened(self, spider):
        self.task = task.LoopingCall(self._log, spider)
        self.task.start(self.interval)

    def _spider_closed(self, spider, reason):
        if self.task.running:
            self.task.stop()

    def _log(self, spider):
        engine = self.crawler.engine
        stats = self.crawler.stats

        if self.first:
            self.first = False
            spider.logger.info(("%8s"*5+"%10s") % (
                "s/edule",
                "d/load",
                "scrape",
                "p/line",
                "done",
                "mem",
                ))

        spider.logger.info(("%8d"*5+"%10d") % (
            len(engine.slot.scheduler.mqs),
            len(engine.downloader.active),
            len(engine.scraper.slot.active),
            engine.scraper.slot.itemproc_size,
            stats.get_value('item_scraped_count') or 0,
            engine.scraper.slot.active_size
            ))
