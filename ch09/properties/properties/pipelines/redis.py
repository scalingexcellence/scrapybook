import json

import dj_redis_url
import txredisapi

from scrapy.exceptions import NotConfigured
from twisted.internet import defer
from scrapy import log
from scrapy import signals


class RedisCache(object):

    @classmethod
    def from_crawler(cls, crawler):
        # Get redis URL
        redis_url = crawler.settings.get('REDIS_PIPELINE_URL', None)

        # If doesn't exist, disable
        if not redis_url:
            raise NotConfigured

        redis_nm = crawler.settings.get('REDIS_PIPELINE_NS', 'ADDRESS_CACHE')

        return cls(crawler, redis_url, redis_nm)

    def __init__(self, crawler, redis_url, redis_nm):
        # Store the url and the namespace for future reference
        self.redis_url = redis_url
        self.redis_nm = redis_nm

        # A method used to report errors
        self.report = log.err

        # Parse redis URL and try to initialize a connection
        args = RedisCache.parse_redis_url(redis_url)
        self.connection = txredisapi.lazyConnectionPool(connectTimeout=5,
                                                        replyTimeout=5,
                                                        **args)

        # Connect the item_scraped signal
        crawler.signals.connect(self.item_scraped, signal=signals.item_scraped)

    @defer.inlineCallbacks
    def process_item(self, item, spider):

        # The item has to have the address field set
        assert ("address" in item) and (len(item["address"]) > 0)

        # Extract the address from the item.
        address = item["address"][0]

        try:
            # Check Redis
            key = self.redis_nm + ":" + address

            value = yield self.connection.get(key)

            if value:
                # Set the value for this item
                item["location"] = json.loads(value)

        except txredisapi.ConnectionError:
            self.report("Can't connect to Redis server: %s" % self.redis_url)
            self.report = lambda _: None  # Deactivate further logging

        defer.returnValue(item)

    def item_scraped(self, item, spider):
        """
        This function inspects the item after it has gone through every
        pipeline stage and if there is some cache value to add it does so.
        """
        # Capture and encode the location and the address
        try:
            location = item["location"]
            value = json.dumps(location, ensure_ascii=False)
        except KeyError:
            return

        # Extract the address from the item.
        address = item["address"][0]

        # Store it in Redis asynchronously
        key = self.redis_nm + ":" + address

        quiet = lambda failure: failure.trap(txredisapi.ConnectionError)

        return self.connection.set(key, value).addErrback(quiet)

    @staticmethod
    def parse_redis_url(redis_url):
        params = dj_redis_url.parse(redis_url)

        conn_kwargs = {}
        conn_kwargs['host'] = params['HOST']
        conn_kwargs['password'] = params['PASSWORD']
        conn_kwargs['dbid'] = params['DB']
        conn_kwargs['port'] = params['PORT']

        # Remove items with empty values
        conn_kwargs = dict((k, v) for k, v in conn_kwargs.iteritems() if v)

        return conn_kwargs
