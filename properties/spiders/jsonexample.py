from scrapy.spider import BaseSpider
from scrapy.selector import HtmlXPathSelector
from scrapy.http import Request

from properties.items import PropertiesItem

import json


class JsonExampleSpider(BaseSpider):
    name = "jsonexample"
    allowed_domains = ["s3.amazonaws.com"]
    start_urls = [
        "http://s3.amazonaws.com/scrapybook/properties/api.json"
    ]

    def parse(self, response):
        js = json.loads(response.body)
        for i in js:
            item = PropertiesItem()
            item['title'] = i["title"]
            
            request = Request("https://s3.amazonaws.com/scrapybook/properties/property_%06d.html" % i["id"], callback=self.parse_details)
            request.meta['item'] = item
            yield request

    def parse_details(self, response):
        hxs = HtmlXPathSelector(response)
        item = response.meta['item']
        item['price'] = hxs.select('//*[@id="primary-h1"]/span[2]/span/text()').extract()[0]
        return item
