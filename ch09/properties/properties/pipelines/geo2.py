import traceback

import treq

from twisted.internet import defer
from twisted.internet import task
from twisted.internet import reactor


class Throttler(object):
    """
    A simple throttler helps you limit the number of requests you make
    to a limited resource
    """

    def __init__(self, rate):
        """It will callback at most ```rate``` enqueued things per second"""
        self.queue = []
        self.looping_call = task.LoopingCall(self._allow_one)
        self.looping_call.start(1. / float(rate))

    def stop(self):
        """Stop the throttler"""
        self.looping_call.stop()

    def throttle(self):
        """
        Call this function to get a deferred that will become available
        in some point in the future in accordance with the throttling rate
        """
        d = defer.Deferred()
        self.queue.append(d)
        return d

    def _allow_one(self):
        """Makes deferred callbacks periodically"""
        if self.queue:
            self.queue.pop(0).callback(None)


class DeferredCache(object):
    """
    A cache that always returns a value, an error or a deferred
    """

    def __init__(self, key_not_found_callback):
        """Takes as an argument """
        self.records = {}
        self.deferreds_waiting = {}
        self.key_not_found_callback = key_not_found_callback

    @defer.inlineCallbacks
    def find(self, key):
        """
        This function either returns something directly from the cache or it
        calls ```key_not_found_callback``` to evaluate a value and return it.
        Uses deferreds to do this is a non-blocking manner.
        """
        # This is the deferred for this call
        rv = defer.Deferred()

        if key in self.deferreds_waiting:
            # We have other instances waiting for this key. Queue
            self.deferreds_waiting[key].append(rv)
        else:
            # We are the only guy waiting for this key right now.
            self.deferreds_waiting[key] = [rv]

            if not key in self.records:
                # If we don't have a value for this key we will evaluate it
                # using key_not_found_callback.
                try:
                    value = yield self.key_not_found_callback(key)

                    # If the evaluation succeeds then the action for this key
                    # is to call deferred's callback with value as an argument
                    # (using Python closures)
                    self.records[key] = lambda d: d.callback(value)
                except Exception as e:
                    # If the evaluation fails with an exception then the
                    # action for this key is to call deferred's errback with
                    # the exception as an argument (Python closures again)
                    self.records[key] = lambda d: d.errback(e)

            # At this point we have an action for this key in self.records
            action = self.records[key]

            # Note that due to ```yield key_not_found_callback```, many
            # deferreds might have been added in deferreds_waiting[key] in
            # the meanwhile
            # For each of the deferreds waiting for this key....
            for d in self.deferreds_waiting.pop(key):
                # ...perform the action later from the reactor thread
                reactor.callFromThread(action, d)

        value = yield rv
        defer.returnValue(value)


class GeoPipeline(object):
    """A pipeline that geocodes addresses using Google's API"""

    @classmethod
    def from_crawler(cls, crawler):
        """Create a new instance and pass it crawler's stats object"""
        return cls(crawler.stats)

    def __init__(self, stats):
        """Initialize empty cache and stats object"""
        self.stats = stats
        self.cache = DeferredCache(self.cache_key_not_found_callback)
        self.throttler = Throttler(5)  # 5 Requests per second

    def close_spider(self, spider):
        """Stop the throttler"""
        self.throttler.stop()

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
    def cache_key_not_found_callback(self, address):
        """
        This method makes an API call while respecting throttling limits.
        It also retries attempts that fail due to limits.
        """
        self.stats.inc_value('geo_pipeline/misses')

        while True:
            # Wait enough to adhere to throttling policies
            yield self.throttler.throttle()

            # Do the API call
            try:
                value = yield self.geocode(address)
                defer.returnValue(value)

                # Success
                break
            except Exception, e:
                if 'status="OVER_QUERY_LIMIT"' in str(e):
                    # Retry in this case
                    self.stats.inc_value('geo_pipeline/retries')
                    continue
                # Propagate the rest
                raise

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
            item["location"] = yield self.cache.find(item["address"][0])
        except:
            self.stats.inc_value('geo_pipeline/errors')
            print traceback.format_exc()

        # Return the item for the next stage
        defer.returnValue(item)
