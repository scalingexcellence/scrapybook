from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.selector import HtmlXPathSelector
from scrapy import signals
from scrapy.xlib.pydispatch import dispatcher

BATCH_SIZE = 1000

class MasterSpider(CrawlSpider):
    name = "master"
    allowed_domains = ["gumtree.com"]
    start_urls = [
        "http://www.gumtree.com/flats-houses/london"
    ]

    rules = (
        Rule(SgmlLinkExtractor(restrict_xpaths=('//*[@id="pagination"]/ul/li/a',)), callback='parse_links', follow=True),
    )

    def __init__(self, *a, **kw):
        super(MasterSpider, self).__init__(*a, **kw)
        dispatcher.connect(self._send_batch, signals.spider_closed)
        self.batch = []

    def _add_to_batch(self, url):
        self.batch.append(url)
        if len(self.batch)>=BATCH_SIZE:
            self._send_batch(None)

    def _send_batch(self,spider):
        if len(self.batch)==0:
            return
        print "just created a batch with size %d" % len(self.batch)
        self.batch=[]

    def parse_links(self, response):
        hxs = HtmlXPathSelector(response)
        #For each link
        for i in hxs.select('//*[@class="description"]/@href'):
            self._add_to_batch(i.extract())

