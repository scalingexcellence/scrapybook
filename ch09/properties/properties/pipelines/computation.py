import time
import threading

from twisted.internet import reactor, defer


class UsingBlocking(object):
    """A pipeline that fakes some computation or blocking calls"""

    def __init__(self):
        """
        This function doesn't need any settings so init just initializes a few
        fields
        """

        self.beta, self.delta = 0, 0
        self.lock = threading.RLock()

    @defer.inlineCallbacks
    def process_item(self, item, spider):
        """We defer a function to Twisted rector's thread pool"""

        # Get the price
        price = item["price"][0]

        # Call a complex/blocking function in a thread pool
        # Note that while this will give you some performance boost
        # it's still subject to GIL and likely won't make the most
        # out of systems with multiple CPUs/cores.
        # Consider Twisted's spawnProcess() (example in legacy.py)
        # or crafting a custom solution around Python's
        # multiprocessing.Process to make the most out of your
        # cores for CPU intensive tasks. Also consider doing this
        # processing as a batch post-processing step as shown in Chapter 11.
        out = defer.Deferred()
        reactor.callInThread(self._do_calculation, price, out)

        # Yield out to get the result and replace the price with it
        item["price"][0] = yield out

        # Return the item to the next stage
        defer.returnValue(item)

    def _do_calculation(self, price, out):
        """
        This is a slow calculation. Notice that it uses locks to protect a
        global state. If you don't use locks and you have global state, your
        will end up with corrupted data
        """

        # Use a lock to protect the critical section
        with self.lock:
            # Faking a complex calculation that uses global state
            self.beta += 1
            # Hold the lock for as little time as possible. Here by sleeping
            # for 1ms we make data corruption in case you don't hold the lock
            # more likely
            time.sleep(0.001)
            self.delta += 1
            new_price = price + self.beta - self.delta + 1

        # Using our "complex" calculation, the end-value must remain the same
        assert abs(new_price - price - 1) < 0.01, "%f!=%f" % (new_price, price)

        # Do some calculations that don't require global state...
        time.sleep(0.10)

        # We enqueue processing the value to the main (reactor's) thread
        reactor.callFromThread(out.callback, new_price)
