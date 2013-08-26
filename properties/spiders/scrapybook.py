from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.loader import XPathItemLoader
from scrapy.contrib.loader.processor import TakeFirst, Identity, MapCompose
from scrapy.selector import HtmlXPathSelector
from scrapy.xlib.pydispatch import dispatcher
from scrapy import signals
from properties.items import PropertiesItem
from w3lib.url import file_uri_to_path
import requests, pickle, socket, re, subprocess, os, random, datetime

BATCH_SIZE = 1000

class ScrapybookSpider(CrawlSpider):
    name = "scrapybook"
    allowed_domains = ["s3.amazonaws.com"]
    start_urls = ["http://s3.amazonaws.com/scrapybook/properties/index_00000.html"]

    index_extractor = SgmlLinkExtractor( restrict_xpaths=('//*[@id="pagination"]/ul/li/a') )
    item_extractor  = SgmlLinkExtractor( restrict_xpaths=('//*[@class="description"]') )
    image_extractor = SgmlLinkExtractor( restrict_xpaths=('//*[@id="gallery-item-mid-1"]/a'), tags=('img'), attrs=('src'), deny_extensions=() )

    rules = (
        Rule(index_extractor),
        Rule(item_extractor, callback='parse_item')
    )

    def __init__(self, mode="standalone", *a, **kw):
        self.mode = mode

        if self.mode == "master":
            self.rules = ( Rule(self.index_extractor, callback='parse_links', follow=True), )
        
        super(ScrapybookSpider, self).__init__(*a, **kw)

        self.log("spider running in %s mode" % self.mode)

        if self.mode=="master":
            # If it's a master spider set some default values
            self.db = getattr(self, "db", "properties")
            self.collection = getattr(self, "collection", "properties")

            # and if a file with workers is given, parse IPs of workers
            try:
                self.workers = filter(None, [line.strip() for line in open(getattr(self, "workers", "workers.txt"))])
            except IOError:
                self.workers = ["localhost"]

            # finaly initialize the batch processing engine
            self.batch = []
            dispatcher.connect(self._send_batch, signals.spider_closed)

        elif self.mode=="worker":
            # If it's a worker spider, process only the URLs given
            if hasattr(self,'url'):
                self.start_urls = [self.url] or self.start_urls if self.url.startswith("http") else pickle.loads(self.url)

            # If parameters for storing to mongodb given, register a spider_closed handler
            if all(getattr(self, i, None) for i in ("mongohost", "db", "collection")):
                dispatcher.connect(self._mongoimport, signals.spider_closed)

            # Instead of using rules for parsing, try to parse an item directly
            self.parse = self.parse_item
    
    def parse_links(self, response):
        # For each link
        for link in self.item_extractor.extract_links(response):
            self._add_to_batch(link.url)

    def parse_item(self, response):

        # Define an ItemLoader that loads PropertiesItem
        # Whenever XPath expressions return an array, get the first item
        # except from breadcrumbs where we want the array itself
        # Cleanup description and cleanup and capitalize properly titles
        class PropertiesItemLoader(XPathItemLoader):
            default_output_processor = TakeFirst()
            breadcrumbs_out          = Identity()
            description_in           = MapCompose(unicode.strip)
            title_in                 = MapCompose(unicode.strip, unicode.title)
        
        # Create the loader using the response
        l = PropertiesItemLoader(item=PropertiesItem(), response=response)

        # Load fields using XPath expressions
        l.add_xpath('title',       '//*[@id="primary-h1"]/span[1]/text()')
        l.add_xpath('price',       '//*[@id="primary-h1"]/span[2]/span/text()')
        l.add_xpath('description', '//*[@id="vip-description-text"]/text()')
        l.add_xpath('address',     '//*[@class="ad-location"]/text()')
        l.add_xpath('breadcrumbs', '//*[@id="breadcrumbs"]/li/a/text()')
        
        # When we can't use XPath's load values directly
        l.add_value('url', response.url)
        l.add_value('project', self.settings.get('BOT_NAME'))
        l.add_value('spider', self.name)
        l.add_value('server', u"%s (%s)" % (socket.gethostname(), socket.gethostbyname(socket.gethostname())))
        l.add_value('date', datetime.datetime.now())

        # In case of images, use the image_extractor to extract the 
        l.add_value('image', [link.url for link in self.image_extractor.extract_links(response)])

        item = l.load_item()

        # Price management
        if not item['price']:
            self.log("%s doesn't have a price" % response.url)
            return

        item['price'] = float(re.sub("[^0-9]", "", re.sub("\..*", "", item['price'].replace(",","")))) / (4.3 if item['price'].endswith("pm") else 1)

        if item['price'] < 0.0:
            self.log("%s has negative price" % response.url)
            return

        item['rank'] = 1.0 / (item['price'] + 1.0)
        
        return item

    def _add_to_batch(self, url):
        self.batch.append(url)
        if len(self.batch)>=BATCH_SIZE:
            self._send_batch(None)

    def _send_batch(self,spider):
        if len(self.batch)==0:
            return
        worker = random.choice(self.workers)
        requests.post("http://%s:6800/schedule.json" % worker , data={
            "project":    self.settings.get('BOT_NAME'),
            "spider":     self.name,
            "mode":       "worker",
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

