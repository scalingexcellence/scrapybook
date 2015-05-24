from scrapy import log
from twisted.internet import defer
from twisted.internet import protocol
from twisted.internet import reactor

class CommandSlot(protocol.ProcessProtocol):
    
    def __init__(self, args):
        self._current_deferred = None
        self._queue = []
        reactor.spawnProcess(self, args[0], args=args)
        
    def legacy_calculate(self, price):
        d = defer.Deferred()
        d.addBoth(self._process_done)
        self._queue.append((price, d))
        self._try_dispatch_top()
        return d

    def _process_done(self, result):
        self._current_deferred = None
        self._try_dispatch_top()
        return result

    def _try_dispatch_top(self):
        if not self._current_deferred and self._queue:
            price, d = self._queue.pop(0)
            self._current_deferred = d
            self.transport.write("%f\n" % price)

    # Overriding from protocol.ProcessProtocol
    def connectionMade(self):
        log.msg("Process started with pid %d" % self.transport.pid, level=log.DEBUG)

    def outReceived(self, data):
        self._current_deferred.callback(float(data))

    def errReceived(self, data):
        log.err('Process[%r]: %s' % (self.transport.pid, data.rstrip()))
        
class Pricing(object):

    @classmethod
    def from_crawler(cls, crawler):
        parallel = crawler.settings.get('LEGACY_PARALLEL', 15)
        args = crawler.settings.get('LEGACY_ARGS', ['properties/pipelines/legacy.sh'])
        return cls(parallel, args)
        
    def __init__(self, parallel, args):
        self.args = args
        self.parallel = parallel
        self.slots = [CommandSlot(self.args) for i in xrange(self.parallel)]
        self.rr = 0
    
    @defer.inlineCallbacks
    def process_item(self, item, spider):
        slot = self.slots[self.rr]
        
        self.rr = (self.rr + 1) % self.parallel

        item["price"][0] = yield slot.legacy_calculate(item["price"][0])
        
        defer.returnValue(item)
