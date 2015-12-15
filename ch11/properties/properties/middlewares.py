import logging
import json
import treq


from scrapy import signals
from scrapy.http import Request
from twisted.internet import defer
from scrapy.spiders import CrawlSpider
from scrapy.exceptions import NotConfigured

logger = logging.getLogger(__name__)


class Distributed(object):

    @classmethod
    def from_crawler(cls, crawler):
        """Passes the crawler to the constructor"""
        return cls(crawler)

    def __init__(self, crawler):
        """Initializes this spider middleware"""

        settings = crawler.settings

        # You can also use spider's custom_settings to customize target
        # rule for each spider
        #
        # custom_settings = {
        #     'DISTRIBUTED_TARGET_RULE': 2
        # }
        #
        self._target = settings.getint('DISTRIBUTED_TARGET_RULE', -1)
        if self._target < 0:
            raise NotConfigured

        # If this is set, it's a worker instance and wills start by using
        # those URLs instead of spider's start_requests().
        self._start_urls = settings.get('DISTRIBUTED_START_URLS', None)
        self.is_worker = self._start_urls is not None

        # The URLs to be batched
        self._urls = []

        # Indicates the target scrapyd to dispatch the next batch to
        self._batch = 1

        # The size of a batch. Defaults to 1000.
        self._batch_size = settings.getint('DISTRIBUTED_BATCH_SIZE', 1000)

        # The feed uri
        self._feed_uri = settings.get('DISTRIBUTED_TARGET_FEED_URL', None)

        # Target scrapyd hosts
        self._targets = settings.get("DISTRIBUTED_TARGET_HOSTS")

        # Can't do much as a master without these
        if not self.is_worker:
            if not self._feed_uri or not self._targets:
                raise NotConfigured

        # Connecting close signal
        crawler.signals.connect(self._closed, signal=signals.spider_closed)

        # A list to wait for before you terminate
        self._scrapyd_submits_to_wait = []

        # A de-duplicator
        self._seen = set()

        # The project
        self._project = settings.get('BOT_NAME')

    def process_start_requests(self, start_requests, spider):
        """
        If it's a worker instance, it uses urls from DISTRIBUTED_START_URLS
        setting instead of spider's start_requests.
        """
        if (not isinstance(spider, CrawlSpider) or not self.is_worker):
            # Case master or inactive. Do default behaviour.
            for x in start_requests:
                yield x

        else:

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
        if not isinstance(spider, CrawlSpider) or self.is_worker:
            for x in result:
                yield x

        else:

            for x in result:
                if not isinstance(x, Request):
                    yield x
                else:
                    rule = x.meta.get('rule')

                    if rule == self._target:
                        self._add_to_batch(spider, x)
                    else:
                        yield x

    @defer.inlineCallbacks
    def _closed(self, spider, reason, signal, sender):
        """
        On close, we flush all remaining URLs and if it's a worker instance,
        it posts all the results to the streaming engine.
        """

        # Submit any remaining URLs
        self._flush_urls(spider)

        r = yield defer.DeferredList(self._scrapyd_submits_to_wait)

        for (success, (debug_data, resp)) in r:
            if not success:
                logger.error("%s: treq request not send" % debug_data)
                continue
            if resp.code != 200:
                body = yield resp.body()
                logger.error("%s: scrapyd request failed: %d. Body: %s" %
                             (debug_data, resp.code, body))
                continue
            ob = yield resp.json()
            if ob["status"] != "ok":
                logger.error("%s: scrapyd operation %s: %s" %
                             (debug_data, ob["status"], ob))

    def _add_to_batch(self, spider, request):
        """
        Adds a Request (URL) to the batch. If we reach DISTRIBUTED_BATCH_SIZE
        we flush the batch.
        """
        url = request.url
        if not url in self._seen:
            self._seen.add(url)
            self._urls.append(url)
            if len(self._urls) >= self._batch_size:
                self._flush_urls(spider)

    def _flush_urls(self, spider):
        """
        Flushes the URLs.
        """
        if not self._urls:
            return

        target = self._targets[(self._batch-1) % len(self._targets)]

        logger.info("Posting batch %d with %d URLs to %s",
                    self._batch, len(self._urls), target)

        data = [
            ("project", self._project),
            ("spider", spider.name),
            ("setting", "FEED_URI=%s" % self._feed_uri),
            ("batch", str(self._batch)),
        ]

        debug_data = "target (%d): %s" % (len(self._urls), data)

        json_urls = json.dumps(self._urls)
        data.append(("setting", "DISTRIBUTED_START_URLS=%s" % json_urls))

        d = treq.post("http://%s/schedule.json" % target,
                      data=data, timeout=5, persistent=False)

        d.addBoth(lambda resp: (debug_data, resp))

        self._scrapyd_submits_to_wait.append(d)

        self._urls = []
        self._batch += 1
