from geopy import geocoders
#from scrapymongocache import MongoCacheBasePipeline, cache


class GeocodingPipeline():#MongoCacheBasePipeline):
    def __init__(self):
        self.geo = geocoders.GoogleV3()

    #@cache("loc_cache.cache", "address", ["location", "geo_addr"])
    def process_item(self, item, spider):
        try:
            item["geo_addr"], (lat, lng) = self.geo.geocode(
                item["address"],
                exactly_one=False
            )[0]
            item["location"] = [lng, lat]
        except:
            pass

        return item
