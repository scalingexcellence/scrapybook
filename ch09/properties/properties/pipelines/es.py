import json
import traceback

import treq

from urllib import quote
from twisted.internet import defer
from scrapy.exceptions import NotConfigured
from twisted.internet.error import ConnectError
from twisted.internet.error import ConnectingCancelledError


class EsWriter(object):
    """A pipeline that writes to Elastic Search"""

    @classmethod
    def from_crawler(cls, crawler):
        """Create a new instance and pass it ES's url"""

        # Get Elastic Search URL
        es_url = crawler.settings.get('ES_PIPELINE_URL', None)

        # If doesn't exist, disable
        if not es_url:
            raise NotConfigured

        return cls(es_url)

    def __init__(self, es_url):
        """Store url and initialize error reporting"""

        # Store the url for future reference
        self.es_url = es_url

    @defer.inlineCallbacks
    def process_item(self, item, spider):
        """
        Pipeline's main method. Uses inlineCallbacks to do
        asynchronous REST requests
        """
        try:
            # Create a json representation of this item
            data = json.dumps(dict(item), ensure_ascii=False).encode("utf-8")
            yield treq.post(self.es_url, data, timeout=5)
        finally:
            # In any case, return the dict for the next stage
            defer.returnValue(item)
