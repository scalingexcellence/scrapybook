from twisted.internet import defer
from treq import get

class GeoPipeline(object):
    """A pipeline that geocodes addresses using Google's API"""

    @classmethod
    def from_crawler(cls, crawler):
        """Create a new instance and pass it crawler's stats object"""
        
        return cls(crawler.stats)
        
    def __init__(self, stats):
        """Initialize empty cache and stats object"""
        
        self.cache = {}
        self.stats = stats

    @defer.inlineCallbacks
    def process_item(self, item, spider):
        """
        Pipeline's main method. Uses inlineCallbacks to do
        asynchronous REST requests
        """
        
        # The item has to have the address field set
        assert "address" in item
        assert len(item["address"]) > 0
                
        # Extract the address from the item.
        address = item["address"][0]
        
        try:
            if "location" in item:
                # Set by previous step (spider or pipeline). Don't do anything
                # apart from increasing stats
                self.stats.inc_value('geo_pipeline/already_set', spider=spider)
            else:
                # Try to use local cache
                item["location"] = self.cache[address]
                
                # Increase the stats
                self.stats.inc_value('geo_pipeline/cache_hit', spider=spider)
                
        except KeyError:
            try:
                # The url for this API
                url = 'https://maps.googleapis.com/maps/api/geocode/json'
                
                # Do the call
                response = yield get(url, params=[('address', address), ('sensor', 'false')])
                
                # Check response code
                if response.code != 200:
                    raise Exception('Response error (code: %d)' % response.code)
                
                # Decode the response as json
                content = yield response.json()
                
                # Extract the address and geo-point and set item's fields
                geo = content['results'][0]["geometry"]["location"]
                item["location"] = {"lat": geo["lat"], "lon": geo["lng"]}
                
                # Cache the results
                self.cache[address] = item["location"]
                
                # Increase the stats
                self.stats.inc_value('geo_pipeline/cache_miss', spider=spider)
                
            except Exception as e:
                # Increase the stats
                self.stats.inc_value('geo_pipeline/error', spider=spider)
                
                item["location"] = {"lat": 0, "lon": 0}
                
                # Intentionally raise these to keep them visible. if it
                # can't find content['results'][0]["formatted_address"]
                # it means that probably we've reached the Google API limit.
                raise
        
        # Return the item for the next stage
        defer.returnValue(item)
