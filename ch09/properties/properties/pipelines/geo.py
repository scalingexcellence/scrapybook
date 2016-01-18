import traceback

import treq

from twisted.internet import defer


class GeoPipeline(object):
    """A pipeline that geocodes addresses using Google's API"""

    @classmethod
    def from_crawler(cls, crawler):
        """Create a new instance and pass it crawler's stats object"""
        return cls(crawler.stats)

    def __init__(self, stats):
        """Initialize empty cache and stats object"""
        self.stats = stats

    @defer.inlineCallbacks
    def geocode(self, address):
        """
        This method makes a call to Google's geocoding API. You shouldn't
        call this more than 5 times per second
        """

        # The url for this API
        #endpoint = 'https://maps.googleapis.com/maps/api/geocode/json'
        endpoint = 'http://web:9312/maps/api/geocode/json'

        # Do the call
        parms = [('address', address), ('sensor', 'false')]
        response = yield treq.get(endpoint, params=parms)

        # Decode the response as json
        content = yield response.json()

        # If the status isn't ok, return it as a string
        if content['status'] != 'OK':
            raise Exception('Unexpected status="%s" for address="%s"' %
                            (content['status'], address))

        # Extract the address and geo-point and set item's fields
        geo = content['results'][0]["geometry"]["location"]

        # Return the final value
        defer.returnValue({"lat": geo["lat"], "lon": geo["lng"]})

    @defer.inlineCallbacks
    def process_item(self, item, spider):
        """
        Pipeline's main method. Uses inlineCallbacks to do
        asynchronous REST requests
        """

        if "location" in item:
            # Set by previous step (spider or pipeline). Don't do anything
            # apart from increasing stats
            self.stats.inc_value('geo_pipeline/already_set')
            defer.returnValue(item)
            return

        # The item has to have the address field set
        assert ("address" in item) and (len(item["address"]) > 0)

        # Extract the address from the item.
        try:
            item["location"] = yield self.geocode(item["address"][0])
        except:
            self.stats.inc_value('geo_pipeline/errors')
            print traceback.format_exc()

        # Return the item for the next stage
        defer.returnValue(item)
