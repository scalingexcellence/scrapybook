# -*- coding: utf-8 -*-
import scrapy
import socket
import datetime
import urlparse
from properties.items import PropertiesItem
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.loader import ItemLoader
from scrapy.contrib.loader.processor import MapCompose, Join
from scrapy.contrib.linkextractors import LinkExtractor


class FastSpider(CrawlSpider):
    name = 'fast'
    #allowed_domains = ['scrapybook.s3.amazonaws.com']
    #start_urls = ['http://scrapybook.s3.amazonaws.com/properties/index_00000.html']
    start_urls = ['http://www.gumtree.com/flats-houses/london']

    rules = (
        Rule(LinkExtractor(
            restrict_xpaths=('//*[contains(@class,"next")]/a',)),
            callback='parse_item', follow=True),
    )

    def parse_start_url(self, response):
        return self.parse_item(response)

    def parse_item(self, response):
        selectors = response.xpath('//*[@itemtype="http://schema.org/Product"]')
        for selector in selectors:
            # Create the loader using the response
            l = ItemLoader(item=PropertiesItem(), selector=selector)

            # Load fields using XPath expressions
            l.add_xpath('title', './/*[@itemprop="name"][1]/text()',
                                 MapCompose(unicode.strip, unicode.title))
            l.add_xpath('price', './/*[@itemprop="price"][1]/text()',
                                 MapCompose(float), re='[.0-9]+')
            l.add_xpath('description', './/*[@itemprop="description"][1]/text()',
                                       MapCompose(unicode.strip), Join())
            l.add_xpath('address',
                        './/*[@itemtype="http://schema.org/Place"][1]/*/text()',
                        MapCompose(unicode.strip))
            l.add_xpath('image_urls',
                        './/*[@itemprop="image"][1]/@src',
                        MapCompose(lambda rel: urlparse.urljoin(response.url, rel)))
            l.add_xpath('url',
                        './/*[@itemprop="url"][1]/@href',
                        MapCompose(lambda rel: urlparse.urljoin(response.url, rel)))
                        
            l.add_value('project', self.settings.get('BOT_NAME'))
            l.add_value('spider', self.name)
            l.add_value('server', (lambda h: h + ' (' + socket.gethostbyname(h) +
                                                 ')')(socket.gethostname()))
            l.add_value('date', datetime.datetime.now())

            yield l.load_item()
