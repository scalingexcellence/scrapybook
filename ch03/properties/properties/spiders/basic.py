import scrapy
import socket
import datetime
from properties.items import PropertiesItem
from scrapy.contrib.loader import ItemLoader
from scrapy.contrib.loader.processor import MapCompose, Join
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor


class BasicSpider(scrapy.Spider):
    name = "basic"
    allowed_domains = ["s3.amazonaws.com"]
    start_urls = (
        'http://s3.amazonaws.com/scrapybook/properties/property_000000.html',
    )

    def parse(self, response):
        """ This function parses a property page.

        @url http://s3.amazonaws.com/scrapybook/properties/property_000000.html
        @returns items 1
        @scrapes title price description address image_urls
        @scrapes url project spider server date
        """

        # Create the loader using the response
        l = ItemLoader(item=PropertiesItem(), response=response)

        # Load fields using XPath expressions
        l.add_xpath('title', '//*[@itemprop="name"][1]/text()',
                             MapCompose(unicode.strip, unicode.title))
        l.add_xpath('price', '//*[@itemprop="price"][1]/text()',
                             MapCompose(float), re='[.0-9]+')
        l.add_xpath('description', '//*[@itemprop="description"][1]/text()',
                                   MapCompose(unicode.strip), Join())
        l.add_xpath('address',
                    '//*[@itemtype="http://schema.org/Place"][1]/text()',
                    MapCompose(unicode.strip))

        # In case of images, use an SgmlLinkExtractor to extract URLs
        image_extractor = SgmlLinkExtractor(
            restrict_xpaths=('//*[@itemprop="image"][1]',),
            tags=('img'), attrs=('src'), deny_extensions=())

        l.add_value('image_urls', image_extractor.extract_links(response),
                    MapCompose(lambda link: link.url))

        # Housekeeping fields
        l.add_value('url', response.url)
        l.add_value('project', self.settings.get('BOT_NAME'))
        l.add_value('spider', self.name)
        l.add_value('server', (lambda h: h + ' (' + socket.gethostbyname(h) +
                                             ')')(socket.gethostname()))
        l.add_value('date', datetime.datetime.now())

        return l.load_item()
