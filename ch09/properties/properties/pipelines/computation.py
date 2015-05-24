import time
import threading

from twisted.internet import reactor, defer

class MultiThreads(object):
    
    def __init__(self):
        self.beta = 0
        self.delta = 0
        self.lock = threading.RLock()
        
    @defer.inlineCallbacks
    def process_item(self, item, spider):
        d = defer.Deferred()
        
        reactor.callInThread(self._do_calculation, item["price"][0], d)

        item["price"][0] = yield d

        defer.returnValue(item)
        
    def _do_calculation(self, price, d):
        with self.lock:
            # A complex calculation that uses global state
            self.beta += 1
            time.sleep(0.001)
            self.delta += 1
            new_price = price + self.beta - self.delta
            
        assert abs(new_price - price) < 0.00001, "%f != %f" % (new_price, price)
        
        reactor.callFromThread(d.callback, new_price)
