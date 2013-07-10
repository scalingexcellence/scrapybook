from scrapy.contrib.spiders import CrawlSpider
from properties.items import PropertiesItem
from scrapy.xlib.pydispatch import dispatcher
from scrapy.selector import HtmlXPathSelector
from datetime import datetime
from scrapy import signals
import socket, re, pickle, subprocess, os

class WorkerSpider(CrawlSpider):
    name = "worker"
    allowed_domains = ["gumtree.com"]

    def __init__(self, url=None, mongohost=None, db=None, collection=None, *a, **kw):
        super(WorkerSpider, self).__init__(*a, **kw)

        # Getting an array of urls
        if url.startswith("http"):
            self.start_urls = [url]
        else:
            self.start_urls = pickle.loads(url)

        # If we want to use mongoimport, we store the extra arguments and listen to the signal
        if mongohost is not None:
            self.mongohost = mongohost
            self.db = db
            self.collection = collection
            dispatcher.connect(self._mongoimport, signals.spider_closed)

    def _mongoimport(self, spider):
        subprocess.call([
            'mongoimport',
            '--host', self.mongohost,
            '--db', self.db,
            '--collection', self.collection,
            '--file', "/var/lib/scrapyd/items/%s/%s/%s.jl" % (
                self.settings.get('BOT_NAME'),
                self.name,
                os.environ['SCRAPY_JOB']
            )
        ])

    def parse(self, response):
        hxs = HtmlXPathSelector(response)
        item = PropertiesItem()

        def maybe0(v): return v[0] if v and len(v)>0 else ""

        item['title'      ] = maybe0(hxs.select('//*[@id="primary-h1"]/span[1]/text()'     ).extract())
        item['price'      ] = maybe0(hxs.select('//*[@id="primary-h1"]/span[2]/span/text()').extract())
        item['description'] = maybe0(hxs.select('//*[@id="vip-description-text"]/text()'   ).extract())
        item['image'      ] = maybe0(hxs.select('//*[@id="gallery-item-mid-1"]/a/img/@src' ).extract())
        item['breadcrumbs'] = hxs.select('//*[@id="breadcrumbs"]/li/a/text()').extract()
        item['url'        ] = response.url
        item['website'    ] = "Gumtree"
        item['address'    ] = maybe0(hxs.select('//*[@class="ad-location"]/text()'         ).extract())
        item['project'    ] = self.settings.get('BOT_NAME')
        item['spider'     ] = self.name
        item['server'     ] = "%s (%s)" % (socket.gethostname(), socket.gethostbyname(socket.gethostname()))
        item['date'       ] = datetime.now()

        # Price management
        if not item['price'].strip():
            self.log('Empty price on %s' % response.url)
            return

        if item['price'].endswith("pm"):
            item['price'] = float(re.sub("[^0-9]", "", item['price'      ]))/4.3
        else:
            item['price'] = float(re.sub("[^0-9]", "", item['price'      ]))

        return item

