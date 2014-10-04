from scrapy.contrib.loader.processor import MapCompose, Join
from scrapy.contrib.linkextractors import LinkExtractor
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.loader import ItemLoader
from properties.items import PropertiesItem
import datetime
import urlparse
import socket


class FastSpider(CrawlSpider):
    name = 'fast'
    allowed_domains = ['scrapybook.s3.amazonaws.com']

    # Start on the first index page
    start_urls = ['http://scrapybook.s3.amazonaws.com/'
                  'properties/index_00000.html']

    # Jump from one index page to the next one
    rules = (
        Rule(LinkExtractor(
            restrict_xpaths=('//*[contains(@class,"next")]/a',)),
            callback='parse_item', follow=True),
    )

    def parse_start_url(self, response):
        # Parse the first URL in the same way as all the rest
        return self.parse_item(response)

    def parse_item(self, response):
        # Iterate through products and create PropertiesItems
        selectors = response.xpath(
            '//*[@itemtype="http://schema.org/Product"]')
        for selector in selectors:
            yield self.parse_single_item(selector, response)

    def parse_single_item(self, selector, response):
        # Create the loader using the selector
        l = ItemLoader(item=PropertiesItem(), selector=selector)

        # Load fields using XPath expressions
        l.add_xpath('title', './/*[@itemprop="name"][1]/text()',
                    MapCompose(unicode.strip, unicode.title))
        l.add_xpath('price', './/*[@itemprop="price"][1]/text()',
                    MapCompose(lambda i: i.replace(',', ''), float),
                    re='[,.0-9]+')
        l.add_xpath('description', './/*[@itemprop="description"][1]/text()',
                    MapCompose(unicode.strip), Join())
        l.add_xpath('address',
                    './/*[@itemtype="http://schema.org/Place"][1]/*/text()',
                    MapCompose(unicode.strip))
        l.add_xpath('image_urls', './/*[@itemprop="image"][1]/@src',
                    MapCompose(lambda i: urlparse.urljoin(response.url, i)))

        # Housekeeping fields
        l.add_xpath('url', './/*[@itemprop="url"][1]/@href',
                    MapCompose(lambda i: urlparse.urljoin(response.url, i)))
        l.add_value('project', self.settings.get('BOT_NAME'))
        l.add_value('spider', self.name)
        l.add_value('server', (lambda i: i + ' (' + socket.gethostbyname(i) +
                                             ')')(socket.gethostname()))
        l.add_value('date', datetime.datetime.now())

        return l.load_item()
