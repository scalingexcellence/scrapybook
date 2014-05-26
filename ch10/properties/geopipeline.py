from geopy import geocoders
from scrapymongocache import MongoCacheBasePipeline, cache


class GeocodingPipeline(MongoCacheBasePipeline):
    def __init__(self):
        self.geo = geocoders.GoogleV3()

    @cache("loc_cache.cache", "address", ["loc", "geo_addr"])
    def process_item(self, item, spider):
        try:
            geo_addr, (lat, lng) = self.geo.geocode(
                item["address"],
                exactly_one=False
            )[0]
            item["loc"] = [lat, lng]
            item["geo_addr"] = geo_addr
        except:
            pass

        return item
