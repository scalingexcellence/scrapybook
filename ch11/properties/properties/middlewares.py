import logging
import json
import treq
import random


from scrapy import signals
from scrapy.http import Request
from twisted.internet import defer
from scrapy.spiders import CrawlSpider
from scrapy.exceptions import NotConfigured

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

        self.settings = crawler.settings

        # You can use spider's custom_settings to customize this one per-spider
        # custom_settings = {
        #     'DISTRIBUTED_TARGET_RULE': 2
        # }
        self._target = self.settings.getint('DISTRIBUTED_TARGET_RULE', -1)
        if self._target < 0:
            raise NotConfigured

        # If this is set, it's a worker instance and wills start by using
        # those URLs instead of spider's start_requests().
        self._start_urls = self.settings.get('DISTRIBUTED_START_URLS', None)

        # The URLs to be batched
        self._urls = set()

        # The size of a batch. Defaults to 1000.
        self._batch_size = self.settings.getint('DISTRIBUTED_BATCH_SIZE', 1000)

        # Connecting close signal
        crawler.signals.connect(self.closed, signal=signals.spider_closed)

    def is_worker(self):
        """Returns True if this is a worker instance"""
        return self._start_urls is not None

    def is_active(self):
        """
        Returns True if the spider midleware is active. Could be inactive
        due to incompatible spider or ivnalid settings
        """
        return self._target >= 0

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
        if (not isinstance(spider, CrawlSpider) or not self.is_active() or not
                self.is_worker()):
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
                          meta={'rule': self._target})

    def process_spider_output(self, response, result, spider):
        """
        If a request is for a traget rule, it gets batched. It passes-through
        otherwise.
        """
        if not isinstance(spider, CrawlSpider) or not self.is_active():
            for x in result:
                yield x
            return

        for x in result:
            if isinstance(x, Request) and x.meta.get('rule') == self._target:
                self.batch_push(spider, x)
            else:
                yield x

    @defer.inlineCallbacks
    def closed(self, spider, reason, signal, sender):
        """
        On close, we flush all remaining URLs and if it's a worker instance,
        it posts all the results to the streaming engine.
        """
        self.flush_urls(spider)

        if self.is_worker():
            url = "http://sandbox:50070/webhdfs/v1/app/map%010d.txt?op=CREATE&user.name=root&overwrite=false" % random.randint(10, 100000)

            feed = self.settings.get('FEED_URI', None).replace('file://', '')
            logger.info("Loading outpout file from %(feed)s",
                        {'feed': feed}, extra={'spider': spider})

            with open(feed, "r") as myfile:
                response = yield treq.put(url, allow_redirects=False)#, )
                assert response.code == 307  # Temporary redirect
                datanode_url = response.headers.getRawHeaders('location')[0]
                response = yield treq.put(datanode_url, myfile.read())
                assert response.code == 201

        #defer.returnValue(None)
