from scrapy.spider import BaseSpider
from scrapy.selector import HtmlXPathSelector, XmlXPathSelector
from scrapy.http import Request
from scrapy import log


class XmlExampleSpider(BaseSpider):
    name = "foaf"
    start_urls = ["http://people.apache.org/committers.html"]

    def parse(self, response):
        hxs = HtmlXPathSelector(response)
        for url in hxs.select('//img[@alt="External FOAF"]/../@href').extract():
            yield Request(url, callback=self.parse_foaf)

    def parse_foaf(self, response):
        try:
            xxs = XmlXPathSelector(response)
            xxs.register_namespace("foaf", "http://xmlns.com/foaf/0.1/")

            info = xxs.select("//foaf:Person[1]/foaf:name/text()").extract()
            if info:
                info = "- " + info[0]
                knows = xxs.select("//foaf:Person[1]//foaf:knows//foaf:name/text()").extract()
                if knows:
                    info += " knows " + ", ".join(knows)
                log.msg(info, level=log.INFO)
        except:
            pass
