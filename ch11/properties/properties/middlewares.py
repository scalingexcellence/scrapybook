import logging
import json

from scrapy import signals
from scrapy.exceptions import NotConfigured
from scrapy.spiders import CrawlSpider
from scrapy.http import Request

logger = logging.getLogger(__name__)

#Call master:
#clear && scrapy crawl easy -s CLOSESPIDER_PAGECOUNT=30
#Call worker:
#curl http://localhost:6800/schedule.json -d project=myproject
#-d spider=somespider -d setting=DISTRIBUTED_START_URLS=[...]
#see also here: https://github.com/scrapy/scrapyd/blob/f4b8cfb40
#12e6562c4cd47486c475b2b0704e807/scrapyd/launcher.py#L40
#clear && scrapy crawl easy -o BOO.jl -s DISTRIBUTED_START_URLS=
#'["http://scrapybook.s3.amazonaws.com/properties/property_000150.html"]'

# If you want to see some real speed 30 seconds for 1666 index pages/50k urls:
#start_urls = ['http://scrapybook.s3.amazonaws.com/properties/index_%05d.html'
#%i for i in xrange(0,1667)]
#clear && time scrapy crawl easy


class Distributed(object):

    @classmethod
    def from_crawler(cls, crawler):
        """Passes the crawler to the constructor"""
        return cls(crawler)

    def __init__(self, crawler):
        """Initializes this spider middleware"""

        # Enable by setting to positive number
        self._batch_size = crawler.settings.getint('DISTRIBUTED_BATCH_SIZE', 0)
        if self._batch_size <= 0:
            raise NotConfigured

        # If this is set, it's a worker instance and wills start by using
        # those URLs instead of spider's start_requests().
        self._start_urls = crawler.settings.get('DISTRIBUTED_START_URLS', None)

        # You can use spider's custom_settings to customize this one per-spider
        # custom_settings = {
        #     'DISTRIBUTED_TARGET_CB': 'my_parse_item'
        # }
        self._target_callback = crawler.settings.get('DISTRIBUTED_TARGET_CB',
                                                     'parse_item')

        # Used by workers
        self._feed_uri = crawler.settings.get('FEED_URI', None)

        # The URLs to be batched
        self._urls = set()

        # Spider middleware inactive by default. It gets enabled in
        # spider_opened() if the spider and settings are suitable.
        self._target_rule = -1

        # Connecting open and close signals
        cs = crawler.signals
        cs.connect(self.spider_opened, signal=signals.spider_opened)
        cs.connect(self.spider_closed, signal=signals.spider_closed)

    def is_worker(self):
        """Returns True if this is a worker instance"""
        return self._start_urls is not None

    def is_active(self):
        """
        Returns True if the spider midleware is active. Could be inactive
        due to incompatible spider or ivnalid settings
        """
        return self._target_rule >= 0

    def spider_opened(self, spider):
        """
        This is the function called when a spider is openned. It checks
        if the spider is a CrawlSpider and then goes through its rules to see
        if there's one that has as callback the one in DISTRIBUTED_TARGET_CB
        setting. If not, the middleware can't do anything so it become inactive
        """

        if not isinstance(spider, CrawlSpider):
            logger.error("Not a CrawlSpiders. Disabling Distributed",
                         extra={'spider': spider})
            return

        def get_method(method):
            if callable(method):
                return method
            elif isinstance(method, basestring):
                return getattr(spider, method, None)

        target_callback = get_method(self._target_callback)

        if not target_callback:
            logger.error("Can't find target method %(target_rule)s. Disabling "
                         "Distributed", {'target_rule': self._target_callback},
                         extra={'spider': spider})
            return

        for n, rule in enumerate(spider.rules):
            if get_method(rule.callback) == target_callback:
                # Implicity becomes active
                self._target_rule = n
                break
        else:  # Yes, this is the weird for...else Python idiom
            logger.error("Can't find rule with %(target_rule)s. Disabling "
                         "Distributed", {'target_rule': self._target_callback},
                         extra={'spider': spider})

    def batch_push(self, spider, request):
        """
        Adds a Request (URL) to the batch. If we reach DISTRIBUTED_BATCH_SIZE
        we flush the batch.
        """
        self._urls.add(request.url)
        if len(self._urls) >= self._batch_size:
            self.flush_urls(spider)

    def flush_urls(self, spider):
        """
        Flushes the URLs.
        """
        if len(self._urls):
            logger.info("Posting job with %(urls_cnt)d URLs",
                        {'urls_cnt': len(self._urls)},
                        extra={'spider': spider})

        self._urls = set()

    def process_start_requests(self, start_requests, spider):
        """
        If it's a worker instance, it uses urls from DISTRIBUTED_START_URLS
        setting instead of spider's start_requests.
        """
        if not self.is_active() or not self.is_worker():
            # Case master or inactive. Do default behaviour.
            for x in start_requests:
                yield x
            return

        # Case worker:
        for url in json.loads(self._start_urls):
            # class scrapy.http.Request(url[, callback, method='GET',
            # headers, body, cookies, meta, encoding='utf-8',
            # priority=0, dont_filter=False, errback])
            # Note: This doesn't take into account headers, cookies,
            # non-GET methods etc.
            yield Request(url, spider._response_downloaded,
                          meta={'rule': self._target_rule})

    def process_spider_output(self, response, result, spider):
        """
        If a request is for a traget rule, it gets batched. It passes-through
        otherwise.
        """
        for x in result:
            if (self.is_active() and isinstance(x, Request) and
                    x.meta.get('rule') == self._target_rule):
                #logger.info("Bathing requests: %(request)s",
                #{'request': x}, extra={'spider': spider})
                self.batch_push(spider, x)
            else:
                yield x

    def spider_closed(self, spider):
        """
        On close, we flush all remaining URLs and if it's a worker instance,
        it posts all the results to the streaming engine.
        """
        self.flush_urls(spider)

        if self.is_worker():
            logger.info("CLOSED WORKER: %(urls)s", {'urls': self._feed_uri},
                        extra={'spider': spider})
