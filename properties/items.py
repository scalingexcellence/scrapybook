from scrapy.item import Item, Field

class PropertiesItem(Item):
    title = Field()
    price = Field()
    description = Field()
    image = Field()
    breadcrumbs = Field()
    url = Field()
    website = Field()
    address = Field()
    loc = Field()
    geo_addr = Field()
    project = Field()
    spider = Field()
    server = Field()
    date = Field()
