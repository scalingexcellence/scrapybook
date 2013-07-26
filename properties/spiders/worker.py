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

    def __init__(self, url=None, *a, **kw):
        super(WorkerSpider, self).__init__(*a, **kw)

        # Getting an array of urls
        if url.startswith("http"):
            self.start_urls = [url]
        else:
            self.start_urls = pickle.loads(url)
        
        # If we want to use mongoimport, we store the extra arguments and listen to the signal
        if all(getattr(self, v, None) for v in ("mongohost", "db", "collection")):
            dispatcher.connect(self._mongoimport, signals.spider_closed)

    def _mongoimport(self, spider):
        if getattr(self, "mongohost", None):
            subprocess.call([
                'mongoimport',
                '--host', self.mongohost,
                '--db', self.db,
                '--collection', self.collection,
                '--file', "/var/lib/scrapyd/items/%s/%s/%s.jl" % (
                    self.settings.get('BOT_NAME'),
                    self.name,
                    os.getenv("SCRAPY_JOB")
                )
            ])

    def parse(self, response):
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

