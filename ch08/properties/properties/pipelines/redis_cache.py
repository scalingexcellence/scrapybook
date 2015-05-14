import txredisapi
import urlparse
from twisted.internet import defer
from scrapy import log
import json
from scrapy import signals


from twisted.internet.task import deferLater
from twisted.internet import reactor

class RedisCache(object):

    @classmethod
    def from_crawler(cls, crawler):
        # Get redis URL
        redis_url = crawler.settings.get('REDIS_PIPELINE_URL', None)
        
        # If doesn't exist, disable
        if not redis_url:
            raise NotConfigured
        
        return cls(crawler, redis_url)

    def __init__(self, crawler, redis_url):
        # Store the url for future reference
        self.redis_url = redis_url
        
        # Parse redis URL and try to initialize a connection
        args = RedisCache.parse_redis_url(redis_url)
        self.connection = txredisapi.lazyConnectionPool(**args)
        
        # Connect the item_scraped signal
        crawler.signals.connect(self.item_scraped, signal=signals.item_scraped)
        
        # Create an empty local cache
        self.cache = {}
            
    @defer.inlineCallbacks
    def process_item(self, item, spider):
        
        if "location" in item:
            defer.returnValue(item)
            return
            
        # The item has to have the address field set
        assert "address" in item
        assert len(item["address"]) > 0
                
        # Extract the address from the item.
        address = item["address"][0]
        
        try:
            # Is it in local cache?
            if self.cache.get(address, None) is not None:
                # Success
                item["location"] = self.cache[address][0]
                item["geo_addr"] = self.cache[address][1]
            else:
                # If not, retrieve value from Redis
                str_value = yield self.connection.get(address)
                if str_value:
                    # Decode the redis value from string
                    location_info = json.loads(str_value)
                    # Save in local cache too
                    self.cache[address] = location_info
                    # Set item's values
                    item["location"] = self.cache[address][0]
                    item["geo_addr"] = self.cache[address][1]
            
        except txredisapi.ConnectionError:
            # Set the level appropriately according to the importance
            # of Redis caching for your application
            log.msg(format="Can't open connection to redis server: %(redis_url)s",
                redis_url = self.redis_url, level=log.DEBUG)
        
        defer.returnValue(item)

    def item_scraped(self, item, spider):
        """ 
        This function inspects the item after it has gone through all
        the pipelines and if there is some cache value to add it does
        so. It adds to local cache and redis.
        """ 
        try:
            # Extract the address from the item.
            address = item["address"][0]
            
            old_value = self.cache.get(address, None)
            new_value = [item["location"], item["geo_addr"]]
            
            # Do we have an update?
            if  old_value != new_value:
                
                # Capture the location and the address
                self.cache[address] = new_value

                # Encode the value
                str_value = json.dumps(self.cache[address])

                # Store it in redis asynchronously
                d = self.connection.set(address, str_value)
                # Suppress connection errors
                d.addErrback(lambda failure: failure.trap(txredisapi.ConnectionError))
                return d
        
        except KeyError:
            pass # This is ok. location/geo_addr not set for item

    @staticmethod
    def parse_redis_url(redis_url):
        # Break down the URL
        parts = urlparse.urlparse(redis_url)
        
        hsplit = parts.netloc.split(':', 1)
        
        # Create an object with arguments
        args = {}
        args['host'] = hsplit.pop(0)
        if hsplit:
            args['port'] = int(hsplit.pop())
    
        if parts.path:
            args['dbid'] = int(parts.path.split('/')[1])
        
        return args
