from scrapy.item import Item, Field


class PropertiesItem(Item):
    title = Field()
    price = Field()
    description = Field()
    image_urls = Field()
    breadcrumbs = Field()
    url = Field()
    address = Field()
    location = Field()
    geo_addr = Field()
    project = Field()
    spider = Field()
    server = Field()
    date = Field()
    images = Field()

