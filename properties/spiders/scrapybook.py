from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.selector import HtmlXPathSelector
from scrapy.xlib.pydispatch import dispatcher
from scrapy.conf import settings
from w3lib.url import file_uri_to_path
from datetime import datetime
from scrapy import signals
from random import choice
import requests, pickle, socket, re, subprocess, os

BATCH_SIZE = 1000

self.rules = (
    Rule(SgmlLinkExtractor(restrict_xpaths=('//*[@id="pagination"]/ul/li/a',)), callback='parse_index', follow=True),
    Rule(SgmlLinkExtractor(restrict_xpaths=('//*[@class="description"]',)))
)

class ScrapybookSpider(CrawlSpider):
    name = "scrapybook"
    allowed_domains = ["s3.amazonaws.com"]

    start_urls = ["https://s3.amazonaws.com/scrapybook/properties/index_00000.html"]

    index_xpaths = ('//*[@id="pagination"]/ul/li/a',)
    item_xpaths  = ('//*[@class="description"]',)

    rules = (
        Rule(SgmlLinkExtractor(restrict_xpaths=self.index_xpaths)),
        Rule(SgmlLinkExtractor(restrict_xpaths=self.item_xpaths), callback='parse_item')
    )

    def __init__(self, mode="standalone", *a, **kw):
        self.mode = mode

        if self.mode == "master":
            self.rules = ( Rule(SgmlLinkExtractor(restrict_xpaths=self.index_xpaths), callback='parse_links', follow=True) )
        
        super(ScrapybookSpider, self).__init__(*a, **kw)

        if self.mode=="worker":
            # If it's a worker spider, process only the URLs given
            self.start_urls = [url] if url.startswith("http") else pickle.loads(url)

            # If parameters for storing to mongodb given, register a spider_closed handler
            if all(getattr(self, i, None) for i in ("mongohost", "db", "collection")):
                dispatcher.connect(self._mongoimport, signals.spider_closed)

        elif self.mode=="master":
            # If it's a master spider set some default values
            self.db = getattr(self, "db", "properties")
            self.collection = getattr(self, "collection", "properties")
            self.workers = getattr(self, "workers", "workers.txt")

            # and if a file with workers is given, parse IPs of workers
            try:
                self.workers = filter(None, [line.strip() for line in open(workers)])
            except IOError:
                self.workers = ["localhost"]

            # finaly initialize the batch processing engine
            self.batch = []
            dispatcher.connect(self._send_batch, signals.spider_closed)

    def parse_links(self, response):
        hxs = HtmlXPathSelector(response)
        # For each link
        for i in hxs.select('//*[@class="description"]/@href'):
            self._add_to_batch(i.extract())

    def parse_item(self, response):
        hxs = HtmlXPathSelector(response)
        item = PropertiesItem()

        pretty_extract = lambda x: "\n".join(x.extract()).strip()

        item['title'      ] = pretty_extract(hxs.select('//*[@id="primary-h1"]/span[1]/text()'     ))
        item['price'      ] = pretty_extract(hxs.select('//*[@id="primary-h1"]/span[2]/span/text()'))
        item['description'] = pretty_extract(hxs.select('//*[@id="vip-description-text"]/text()'   ))
        item['image'      ] = pretty_extract(hxs.select('//*[@id="gallery-item-mid-1"]/a/img/@src' ))
        item['breadcrumbs'] = hxs.select('//*[@id="breadcrumbs"]/li/a/text()').extract()
        item['url'        ] = response.url
        item['website'    ] = "Gumtree"
        item['address'    ] = pretty_extract(hxs.select('//*[@class="ad-location"]/text()'         ))
        item['project'    ] = self.settings.get('BOT_NAME')
        item['spider'     ] = self.name
        item['server'     ] = "%s (%s)" % (socket.gethostname(), socket.gethostbyname(socket.gethostname()))
        item['date'       ] = datetime.now()

        # Price management
        if not item['price']:
            self.log("%s doesn't have a price" % response.url)
            return

        item['price'] = float(re.sub("[^0-9]", "", item['price'])) / (4.3 if item['price'].endswith("pm") else 1)

        return item

    def _add_to_batch(self, url):
        self.batch.append(url)
        if len(self.batch)>=BATCH_SIZE:
            self._send_batch(None)

    def _send_batch(self,spider):
        if len(self.batch)==0:
            return
        worker = choice(self.workers)
        requests.post("http://%s:6800/schedule.json" % worker , data={
            "project":    self.settings.get('BOT_NAME'),
            "spider":     self.name,
            "url":        pickle.dumps(self.batch),
            "mongohost":  socket.gethostbyname(socket.gethostname()),
            "db":         self.db,
            "collection": self.collection
        })
        print "just scheduled a batch with size %d -> %s" % (len(self.batch), worker)
        self.batch=[]

    def _mongoimport(self, spider):
        subprocess.call([
            'mongoimport',
            '--host', self.mongohost,
            '--db', self.db,
            '--collection', self.collection,
            '--file', file_uri_to_path(self.settings.get('FEED_URI'))
        ])

