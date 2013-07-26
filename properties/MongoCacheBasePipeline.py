from pymongo import MongoClient
from scrapy import log

# A decorator for caching with mongodb
def cache(db_collection, key_field, value_fields):
    def wrapper(original):
        def process_item(self, item, spider):

            # Cache is disabled
            if not getattr(self, "client", None):
                return original(self, item, spider)

            # Select the collection to use for caching
            (db_name,collection_name) = db_collection.split(".")
            collection = self.client[db_name][collection_name]

            # See if an entry for this key already exists
            cached = collection.find_one({key_field: item[key_field]})
            if cached:
                # If yes restore any available values
                for key in set(value_fields) & set(cached.keys()):
                    item[key] = cached[key]
                log.msg("%s found an entry with %s='%s' in the cache" % (self.__class__.__name__, key_field, item[key_field]), level=log.DEBUG)
            else:
                # Else call the underlying method
                item = original(self, item, spider)
                # and add to the cache any available values
                collection.insert( dict([(f,item[f]) for f in set(value_fields+[key_field]) & set(item.keys())]))

            return item

        return process_item
    return wrapper

# A base class to manage the MongoDB connection
class MongoCacheBasePipeline(object):
    
    def open_spider(self, spider):
        mongohost = getattr(spider, "mongohost", "localhost")
        try:
            self.client = MongoClient(host=mongohost)
        except:
            log.msg("%s runs without caching because we can't find mongodb at '%s'" % (self.__class__.__name__, mongohost), level=log.WARNING)

    def close_spider(self, spider):
        if getattr(self, "client", None):
            self.client.disconnect()

