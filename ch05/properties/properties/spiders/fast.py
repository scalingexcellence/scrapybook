import datetime
import urlparse
import socket
import scrapy

from scrapy.loader.processors import MapCompose, Join
from scrapy.loader import ItemLoader
from scrapy.http import Request

from properties.items import PropertiesItem


class BasicSpider(scrapy.Spider):
    name = 'fast'
    allowed_domains = ["web"]

    # Start on the first index page
    start_urls = (
        'http://web:9312/properties/index_00000.html',
    )

    def parse(self, response):
        # Get the next index URLs and yield Requests
        next_selector = response.xpath('//*[contains(@class,"next")]//@href')
        for url in next_selector.extract():
            yield Request(urlparse.urljoin(response.url, url))

        # Iterate through products and create PropertiesItems
        selectors = response.xpath(
            '//*[@itemtype="http://schema.org/Product"]')
        for selector in selectors:
            yield self.parse_item(selector, response)

    def parse_item(self, selector, response):
        # Create the loader using the selector
        l = ItemLoader(item=PropertiesItem(), selector=selector)

        # Load fields using XPath expressions
        l.add_xpath('title', './/*[@itemprop="name"][1]/text()',
                    MapCompose(unicode.strip, unicode.title))
        l.add_xpath('price', './/*[@itemprop="price"][1]/text()',
                    MapCompose(lambda i: i.replace(',', ''), float),
                    re='[,.0-9]+')
        l.add_xpath('description',
                    './/*[@itemprop="description"][1]/text()',
                    MapCompose(unicode.strip), Join())
        l.add_xpath('address',
                    './/*[@itemtype="http://schema.org/Place"]'
                    '[1]/*/text()',
                    MapCompose(unicode.strip))
        make_url = lambda i: urlparse.urljoin(response.url, i)
        l.add_xpath('image_urls', './/*[@itemprop="image"][1]/@src',
                    MapCompose(make_url))

        # Housekeeping fields
        l.add_xpath('url', './/*[@itemprop="url"][1]/@href',
                    MapCompose(make_url))
        l.add_value('project', self.settings.get('BOT_NAME'))
        l.add_value('spider', self.name)
        l.add_value('server', socket.gethostname())
        l.add_value('date', datetime.datetime.now())

        return l.load_item()
