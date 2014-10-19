from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.contrib.loader import ItemLoader
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
        class PropertiesItemLoader(ItemLoader):
            default_output_processor = TakeFirst()
            breadcrumbs_out = Identity()
            image_urls_out = Identity()
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

        # In case of images, use an SgmlLinkExtractor to extract the src URL
        image_extractor = SgmlLinkExtractor(
            restrict_xpaths=('//*[@id="gallery-item-mid-1"]/a',),
            tags=('img'), attrs=('src'), deny_extensions=()
        )
        # Since image isn't extracted via XPath, we can load it's value directly
        l.add_value(
            'image_urls',
            [link.url for link in image_extractor.extract_links(response)]
        )

        return self.set_common(l.load_item(), response)

    # Some fields that are commonly used
    def set_common(self, item, response):
        item['url'] = response.url
        item['project'] = self.settings.get('BOT_NAME')
        item['spider'] = self.name
        item['server'] = socket.gethostname()
        item['date'] = datetime.datetime.now()
        return item
        
ScrapybookSpiderMaster, ScrapybookSpiderWorker = distr(ScrapybookSpider)
