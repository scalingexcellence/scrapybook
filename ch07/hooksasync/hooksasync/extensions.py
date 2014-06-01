from scrapy import log, signals
from scrapy.exceptions import DropItem

from twisted.internet import defer, reactor, task

vote_signal = object()
vote_signal_defered = object()

class HooksasyncExtension(object):
    @classmethod
    def from_crawler(cls, crawler):
        log.msg("HooksasyncExtension from_crawler")
        
        #if not crawler.settings.getbool('HOOKSASYNCEXTENSION_ENABLED'):
        #    raise NotConfigured
        
        # Here the constructor is actually called and the class returned
        return cls(crawler)
    
    def __init__(self, crawler):
        log.msg("HooksasyncExtension Constructor called")
        
        self.crawler = crawler
        
        setting = crawler.settings.getint('HOOKSASYNCEXTENSION_SETTING', 0)
        log.msg("my extension setting is %d" % setting)
        
        # connect the extension object to signals
        crawler.signals.connect(lambda i: log.msg("HooksasyncExtension, signals.engine_started fired"), signal=signals.engine_started)
        crawler.signals.connect(lambda i: log.msg("HooksasyncExtension, signals.engine_stopped fired"), signal=signals.engine_stopped)
        crawler.signals.connect(lambda i: log.msg("HooksasyncExtension, signals.spider_opened fired"), signal=signals.spider_opened)
        crawler.signals.connect(lambda i: log.msg("HooksasyncExtension, signals.spider_idle fired"), signal=signals.spider_idle)
        crawler.signals.connect(lambda i: log.msg("HooksasyncExtension, signals.spider_closed fired"), signal=signals.spider_closed)
        crawler.signals.connect(lambda i: log.msg("HooksasyncExtension, signals.spider_error fired"), signal=signals.spider_error)
        crawler.signals.connect(lambda i: log.msg("HooksasyncExtension, signals.request_scheduled fired"), signal=signals.request_scheduled)
        crawler.signals.connect(lambda i: log.msg("HooksasyncExtension, signals.response_received fired"), signal=signals.response_received)
        crawler.signals.connect(lambda i: log.msg("HooksasyncExtension, signals.response_downloaded fired"), signal=signals.response_downloaded)
        crawler.signals.connect(lambda i: log.msg("HooksasyncExtension, signals.item_scraped fired"), signal=signals.item_scraped)
        crawler.signals.connect(lambda i: log.msg("HooksasyncExtension, signals.item_dropped fired"), signal=signals.item_dropped)
        
        crawler.signals.connect(self.vote_signal1, signal=vote_signal)
        crawler.signals.connect(self.vote_signal2, signal=vote_signal)
        
        crawler.signals.connect(self.vote_signal1defered, signal=vote_signal_defered)
        crawler.signals.connect(self.vote_signal2defered, signal=vote_signal_defered)
        
    def vote_signal1(self, item):
        log.msg("HooksasyncExtension, my vote_signal1 fired for item %s" % item['name'])
        return 5

    def vote_signal2(self, item):
        log.msg("HooksasyncExtension, my vote_signal2 fired for item %s" % item['name'])
        return 3
    
    def vote_signal1defered(self, item):
        log.msg("HooksasyncExtension, my vote_signal1defered fired for item %s" % item['name'])
        return task.deferLater(reactor, 2, lambda item: 2, item)

    def vote_signal2defered(self, item):
        log.msg("HooksasyncExtension, my vote_signal2defered fired for item %s" % item['name'])
        return task.deferLater(reactor, 2, lambda item: 3, item)
        
    def spider_opened(self, spider):
        log.msg("HooksasyncExtension spider_opened")

    def spider_closed(self, spider):
        log.msg("HooksasyncExtension spider_closed")
        
    @classmethod
    def from_settings(cls, settings):
        log.msg("HooksasyncExtension from_settings")
        # This is never called - but would be called if from_crawler()
        # didn't exist. from_crawler() can access the settings via
        # crawler.settings but also has access to everything that
        # crawler object provides like signals, stats and the ability
        # to schedule new requests with crawler.engine.download()

class HooksasyncDownloaderMiddleware(object):
    """ Downloader middlewares *are* extensions and as a result can do
    everything any extension can do (see HooksasyncExtension).
    The main thing that makes them different are the process_*() methods"""

    @classmethod
    def from_crawler(cls, crawler):
        log.msg("HooksasyncDownloaderMiddleware from_crawler")
        # Here the constructor is actually called and the class returned
        return cls(crawler)

    def __init__(self, crawler):
        log.msg("HooksasyncDownloaderMiddleware Constructor called")

        self.crawler = crawler

        setting = crawler.settings.getint('HOOKSASYNCDOWNLOADERMIDDLEWARE_SETTING', 0)
        log.msg("my downloader middleware setting is %d" % setting)

    def process_request(self, request, spider):
        log.msg("HooksasyncDownloaderMiddleware process_request called for %s" % request.url)

    def process_response(self, request, response, spider):
        log.msg("HooksasyncDownloaderMiddleware process_response called for %s" % request.url)
        return response

    def process_exception(self, request, exception, spider):
        log.msg("HooksasyncDownloaderMiddleware process_exception called for %s" % request.url)

class HooksasyncSpiderMiddleware(object):
    """ Spider middlewares *are* extensions and as a result can do
    everything any extension can do (see HooksasyncExtension).
    The main thing that makes them different are the process_*() methods"""

    @classmethod
    def from_crawler(cls, crawler):
        log.msg("HooksasyncSpiderMiddleware from_crawler")
        # Here the constructor is actually called and the class returned
        return cls(crawler)

    def __init__(self, crawler):
        log.msg("HooksasyncSpiderMiddleware Constructor called")

        self.crawler = crawler

        setting = crawler.settings.getint('HOOKSASYNCSPIDERMIDDLEWARE_SETTING', 0)
        log.msg("my spider middleware setting is %d" % setting)

    def process_spider_input(self, response, spider):
        log.msg("HooksasyncSpiderMiddleware process_spider_input called for %s" % response.url)

    def process_spider_output(self, response, result, spider):
        log.msg("HooksasyncSpiderMiddleware process_spider_output called for %s" % response.url)
        return result

    def process_spider_exception(self, response, exception, spider):
        log.msg("HooksasyncSpiderMiddleware process_spider_exception called for %s" % response.url)

    def process_start_requests(self, start_requests, spider):
        log.msg("HooksasyncSpiderMiddleware process_start_requests called")
        return start_requests


class HooksasyncPipeline(object):
    """ Pipelines *are* extensions and as a result can do
    everything any extension can do (see HooksasyncExtension).
    The main thing that makes them different is that they have
    the process_item() method"""

    @classmethod
    def from_crawler(cls, crawler):
        log.msg("HooksasyncPipeline from_crawler")
        # Here the constructor is actually called and the class returned
        return cls(crawler)

    def __init__(self, crawler):
        log.msg("HooksasyncPipeline Constructor called")

        self.crawler = crawler

        setting = crawler.settings.getint('HOOKSASYNCPIPELINE_SETTING', 0)
        log.msg("my spider setting is %d" % setting)

    def process_item(self, item, spider):
        log.msg("HooksasyncPipeline process_item() called for item: %s" % item['name'])

        if (' - 2' in item['name']):
            raise DropItem("I don't like two's")

        return item
