from scrapy.contrib.loader.processor import MapCompose, Join
from scrapy.contrib.loader import ItemLoader
from properties.items import PropertiesItem
import datetime
import urlparse
import socket
import scrapy


class BasicSpider(scrapy.Spider):
    name = "basic"
    allowed_domains = ["scrapybook.s3.amazonaws.com"]
    
    # Start on a property page
    start_urls = (
        'http://scrapybook.s3.amazonaws.com/properties/property_000000.html',
    )

    def parse(self, response):
        """ This function parses a property page.

        @url http://scrapybook.s3.amazonaws.com/properties/property_000000.html
        @returns items 1
        @scrapes title price description address image_urls
        @scrapes url project spider server date
        """

        # Create the loader using the response
        l = ItemLoader(item=PropertiesItem(), response=response)

        # Load fields using XPath expressions
        l.add_xpath('title', '//*[@itemprop="name"][1]/text()',
                    MapCompose(unicode.strip, unicode.title))
        l.add_xpath('price', './/*[@itemprop="price"][1]/text()',
                    MapCompose(lambda p: p.replace(',', ''), float),
                    re='[,.0-9]+')
        l.add_xpath('description', '//*[@itemprop="description"][1]/text()',
                    MapCompose(unicode.strip), Join())
        l.add_xpath('address',
                    '//*[@itemtype="http://schema.org/Place"][1]/text()',
                    MapCompose(unicode.strip))
        l.add_xpath('image_urls',
                    '//*[@itemprop="image" '
                    'and string-length(@src)>0][1]/@src',
                    MapCompose(lambda rel: urlparse.urljoin(response.url, rel))
                    )

        # Housekeeping fields
        l.add_value('url', response.url)
        l.add_value('project', self.settings.get('BOT_NAME'))
        l.add_value('spider', self.name)
        l.add_value('server', (lambda h: h + ' (' + socket.gethostbyname(h) +
                                             ')')(socket.gethostname()))
        l.add_value('date', datetime.datetime.now())

        return l.load_item()
