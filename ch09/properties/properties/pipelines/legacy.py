import logging

from twisted.internet import defer
from twisted.internet import protocol
from twisted.internet import reactor


class CommandSlot(protocol.ProcessProtocol):
    """A ProcessProtocol that sends prices through a binary"""

    def __init__(self, args):
        """Initalizing members and starting a new process"""

        self._current_deferred = None
        self._queue = []
        reactor.spawnProcess(self, args[0], args)

        self.logger = logging.getLogger('pricing-pipeline')

    def legacy_calculate(self, price):
        """Enqueue a price to be calculated"""

        d = defer.Deferred()
        d.addBoth(self._process_done)
        self._queue.append((price, d))
        self._try_dispatch_top()
        return d

    def _process_done(self, result):
        """Called when a calculation completes. It returns the value"""

        self._current_deferred = None
        self._try_dispatch_top()
        return result

    def _try_dispatch_top(self):
        """Starts a new computation by sending a price to the process"""

        if not self._current_deferred and self._queue:
            price, d = self._queue.pop(0)
            self._current_deferred = d
            self.transport.write("%f\n" % price)

    # Overriding from protocol.ProcessProtocol
    def outReceived(self, data):
        """Called when new output is received"""
        self._current_deferred.callback(float(data))

    def errReceived(self, data):
        """Called in case of an error"""
        self.logger.error('PID[%r]: %s' % (self.transport.pid, data.rstrip()))


class Pricing(object):
    """A pipeline that accesses legacy functionality"""

    @classmethod
    def from_crawler(cls, crawler):
        """Create a new instance from settings"""

        concurrency = crawler.settings.get('LEGACY_CONCURENCY', 16)
        default_args = ['properties/pipelines/legacy.sh']
        args = crawler.settings.get('LEGACY_ARGS', default_args)

        return cls(concurrency, args)

    def __init__(self, concurrency, args):
        """Init this instance by the settings"""
        self.args = args
        self.concurrency = concurrency
        self.slots = [CommandSlot(self.args) for i in xrange(self.concurrency)]
        self.rr = 0

    @defer.inlineCallbacks
    def process_item(self, item, spider):
        slot = self.slots[self.rr]

        self.rr = (self.rr + 1) % self.concurrency

        item["price"][0] = yield slot.legacy_calculate(item["price"][0])

        defer.returnValue(item)
