from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.selector import HtmlXPathSelector
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals
from random import choice
import requests, pickle, socket

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

    def __init__(self, workers="workers.txt", *a, **kw):
        super(MasterSpider, self).__init__(*a, **kw)
        dispatcher.connect(self._send_batch, signals.spider_closed)
        self.batch = []
        try:
            self.workers = filter(None, [line.strip() for line in open(workers)])
        except IOError:
            self.workers = ["localhost"]

    def _add_to_batch(self, url):
        self.batch.append(url)
        if len(self.batch)>=BATCH_SIZE:
            self._send_batch(None)

    def _send_batch(self,spider):
        if len(self.batch)==0:
            return
        worker = choice(self.workers)
        print "just scheduled a batch with size %d -> %s" % (len(self.batch), worker)
        self._schedule(worker,"properties","worker",pickle.dumps(self.batch),socket.gethostbyname(socket.gethostname()),"properties","properties")
        self.batch=[]

    def _schedule(self,host,project,spider,url,mongohost,db,collection):
        return requests.post("http://%s:6800/schedule.json" % host , data={
            "project":project,
            "spider":spider,
            "url":url,
            "mongohost":mongohost,
            "db":db,
            "collection":collection
        })

    def parse_links(self, response):
        hxs = HtmlXPathSelector(response)
        #For each link
        for i in hxs.select('//*[@class="description"]/@href'):
            self._add_to_batch(i.extract())

