from scrapy.spider import Spider
from scrapy import log
from twisted.internet import defer, reactor, task
from twisted.python import failure
import time

from hooksasync.items import HooksasyncItem
from hooksasync.extensions import vote_signal, vote_signal_defered

class TestSpider(Spider):
    name = "test"
    allowed_domains = ["example.com"]
    start_urls = (
        'http://www.example.com/?test=1',
#        'http://www.example.com/?test=2',
#        'http://www.example.com/?test=3',
        )

    def parse(self, response):
        dfds = []
        for i in range(3):
            item = HooksasyncItem()
            item['name'] = '%s - %d' % (response.url, i)
            
            item['rate'] = [i[1] for i in self.crawler.signals.send_catch_log(vote_signal, item=item, spider=self)]
            
            def later(reply):
                log.msg("Reseting vote for item: %s" % item['name'], level=log.INFO)
                item['rate'] = [i[1] for i in reply]
                
            dfds.append(self.crawler.signals.send_catch_log_deferred(vote_signal_defered, item=item, spider=self).addCallback(later))

            def a(item):
                log.msg("inside a for item: %s" % item['name'], level=log.INFO)
                item['name'] = item['name'] + ' after a'
                return item
            def b(item):
                log.msg("inside b for item: %s" % item['name'], level=log.INFO)
                item['name'] = item['name'] + ' after b'
                return item
            
            @defer.inlineCallbacks
            def c(item):
                log.msg("inside c for item: %s" % item['name'], level=log.INFO)
                tmp = yield task.deferLater(reactor, 3, lambda i: i, item)
                log.msg("Done processing: %s" % tmp['name'], level=log.INFO)
                defer.returnValue(tmp)

            log.msg("before deferLater for item: %s" % item['name'], level=log.INFO)
            d = task.deferLater(reactor, 5, a, item).addCallback(b).addCallback(c)
            log.msg("after deferLater for item: %s" % item['name'], level=log.INFO)
            dfds.append(d)
        # You can't yield a defered
        return defer.DeferredList(dfds).addCallback(lambda success_and_item: [i[1] for i in success_and_item])
