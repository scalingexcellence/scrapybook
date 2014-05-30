import urllib
import json

from scrapy.http import Request
from scrapy import log
from twisted.internet import defer

def formatGGeocodingV3Url(address):
    parameters = urllib.urlencode({
        "address": address.encode('utf-8'),
        "sensor": "false",
    })
    return "https://maps.googleapis.com/maps/api/geocode/json?%s" % parameters
    
def decodeGGeocodingV3Body(body):
    """
    Decodes the body of a request got from google geocoding
    >>> import requests
    >>> decodeGGeocodingV3Body(requests.get(formatGGeocodingV3Url('London')).text)
    (u'London, UK', [51.508515, -0.1254872])
    """
    r = json.loads(body)
    if r.get('error_message'):
        raise Exception("API error '%s'" % r['error_message'])
    first = r['results'][0]
    location = first["geometry"]["location"]
    return first["formatted_address"], [location["lng"], location["lat"]]

class GeocodingPipeline(object):

    """Just grab the crawler"""
    @classmethod
    def from_crawler(cls, crawler):
        try:
            pipe = cls.from_settings(crawler.settings)
        except AttributeError:
            pipe = cls()
        pipe.crawler = crawler
        return pipe

    @defer.inlineCallbacks
    def process_item(self, item, spider):
        address = item["address"]
        request = Request(formatGGeocodingV3Url(address))
        try:
            response = yield self.crawler.engine.download(request, spider)
            if response.status != 200:
                raise Exception('Response error (code: %s)' % response.status)

            if not response.body:
                raise Exception('empty-content')

            item["geo_addr"], item["location"] = decodeGGeocodingV3Body(response.body)

        except Exception as e:
            log.msg(format="%(error)s: address: '%(address)s', request %(request)s",
                level=log.WARNING, spider=spider, error=str(e), request=request, address=address)
        finally:
            defer.returnValue(item)
    
    def process_item2(self, item, spider):

        address = item["address"]

        request = Request(formatGGeocodingV3Url(address))
        
        dfd = self.crawler.engine.download(request, spider)
        
        dfd.addCallbacks(
            callback = self.downloaded, callbackArgs=(request, address, item, spider),
            errback = lambda: item
        )
        
        return dfd
        
    def downloaded(self, response, request, address, item, spider):
        try:
            if response.status != 200:
                raise Exception('Response error (code: %s)' % response.status)

            if not response.body:
                raise Exception('empty-content') 
            
            item["geo_addr"], item["location"] = decodeGGeocodingV3Body(response.body)

        except Exception as e:
            log.msg(format="%(error)s: address: '%(address)s', request %(request)s",
                        level=log.WARNING, spider=spider, error=str(e), request=request, address=address)
        return item
        
if __name__ == "__main__":
    import doctest
    doctest.testmod()

