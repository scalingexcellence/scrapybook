from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.loader import XPathItemLoader
from scrapy.contrib.loader.processor import TakeFirst, Identity, MapCompose
from properties.items import PropertiesItem
from properties.spiders.distributed import distr

import socket
import datetime


class ScrapybookSpider(CrawlSpider):
    name = "scrapybook"
    allowed_domains = ["s3.amazonaws.com"]
    start_urls = [
        "http://s3.amazonaws.com/scrapybook/properties/index_00000.html"
    ]

    index_extractor = SgmlLinkExtractor(
        restrict_xpaths=('//*[@id="pagination"]/ul/li/a',)
    )
    item_extractor = SgmlLinkExtractor(
        restrict_xpaths=('//*[@class="description"]',)
    )

    rules = (
        Rule(index_extractor),
        Rule(item_extractor, callback='parse_item')
    )

    def parse_item(self, response):

        # Define an ItemLoader that loads PropertiesItem
        # Whenever XPath expressions return an array, get the first item
        # except from breadcrumbs where we want the array itself
        # Cleanup description and cleanup and capitalize properly titles
        class PropertiesItemLoader(XPathItemLoader):
            default_output_processor = TakeFirst()
            breadcrumbs_out = Identity()
            description_in = MapCompose(unicode.strip)
            title_in = MapCompose(unicode.strip, unicode.title)

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
        hn = socket.gethostname()
        l.add_value('server', u"%s (%s)" % (hn, socket.gethostbyname(hn)))
        l.add_value('date', datetime.datetime.now())

        # In case of images, use an SgmlLinkExtractor to extract the src URL
        image_extractor = SgmlLinkExtractor(
            restrict_xpaths=('//*[@id="gallery-item-mid-1"]/a',),
            tags=('img'), attrs=('src'), deny_extensions=()
        )
        l.add_value(
            'image',
            [link.url for link in image_extractor.extract_links(response)]
        )

        return l.load_item()

ScrapybookSpiderMaster, ScrapybookSpiderWorker = distr(ScrapybookSpider)
