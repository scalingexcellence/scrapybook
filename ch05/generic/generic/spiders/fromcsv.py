import csv

import scrapy
from scrapy.http import Request
from scrapy.loader import ItemLoader
from scrapy.item import Item, Field


class FromcsvSpider(scrapy.Spider):
    name = "fromcsv"

    def start_requests(self):
        with open(getattr(self, "file", "todo.csv"), "rU") as f:
            reader = csv.DictReader(f)
            for line in reader:
                request = Request(line.pop('url'))
                request.meta['fields'] = line
                yield request

    def parse(self, response):
        item = Item()
        l = ItemLoader(item=item, response=response)
        for name, xpath in response.meta['fields'].iteritems():
            if xpath:
                item.fields[name] = Field()
                l.add_xpath(name, xpath)

        return l.load_item()
