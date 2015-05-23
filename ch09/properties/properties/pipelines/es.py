import json
from datetime import datetime

from treq import put

from scrapy import log
from urllib import quote
from twisted.internet import defer
from twisted.internet.error import ConnectError
from twisted.internet.error import ConnectionRefusedError

class EsWriter(object):

    @classmethod
    def from_crawler(cls, crawler):
        # Get Elastic Search URL
        es_url = crawler.settings.get('ES_PIPELINE_URL', None)
        
        # If doesn't exist, disable
        if not es_url:
            raise NotConfigured
        
        return cls(es_url)
        
    def __init__(self, es_url):
        self.es_url = es_url
        self.report = log.err
    
    @defer.inlineCallbacks
    def process_item(self, item, spider):
        try:
            # Item isn't JSON serializable. dict(item) is though.
            document = dict(item)
    
            # Make the date JSON serializable by converting it to isoformat
            document['date'] = map(datetime.isoformat, document['date'])
    
            # Extract the ID (it's the URL)
            id = document['url'][0]
            
            # Make the request
            yield put('%s/%s' % (self.es_url, quote(str(id), '')), json.dumps(document))
        
        except ConnectError:
            self.report("Can't open connection to elastic search server: %s" % self.es_url)
            self.report = lambda _: None # Deactivate further logging
        
        finally:
            # Return the item for the next stage
            defer.returnValue(item)
