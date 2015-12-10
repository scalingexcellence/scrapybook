#!/usr/bin/env python

# ~*~ Understanding Twisted deferreds ~*~


def example0():
    from twisted.internet import defer

    # Experiment 1
    d = defer.Deferred()
    d.called
    d.callback(3)
    d.called
    d.result

    # Experiment 2
    d = defer.Deferred()

    def foo(v):
        print "foo called"
        return v+1

    d.addCallback(foo)
    d.called
    d.callback(3)
    d.called
    d.result

    # Experiment 3
    def status(*ds):
        return [(getattr(d, 'result', "N/A"), len(d.callbacks)) for d in ds]

    def b_callback(arg):
        print "b_callback called with arg =", arg
        return b

    def on_done(arg):
        print "on_done called with arg =", arg
        return arg

    # Experiment 3.a
    a = defer.Deferred()
    b = defer.Deferred()

    a.addCallback(b_callback).addCallback(on_done)

    status(a, b)

    a.callback(3)

    status(a, b)

    b.callback(4)

    status(a, b)

    # Experiment 3.b
    a = defer.Deferred()
    b = defer.Deferred()

    a.addCallback(b_callback).addCallback(on_done)

    b.callback(4)

    status(a, b)

    a.callback(3)

    status(a, b)

    # Experiment 4
    deferreds = [defer.Deferred() for i in xrange(5)]
    join = defer.DeferredList(deferreds)
    join.addCallback(on_done)
    for i in xrange(4):
        deferreds[i].callback(i)

    deferreds[4].callback(4)

from time import sleep


# ~*~ Twisted - A Python tale ~*~


# Hello, I'm a developer and I mainly setup Wordpress.
def install_wordpress(customer):
    # Our hosting company Threads Ltd. sucks. I start installation and...
    print "Start installation for", customer

    # ...then wait till the installation finishes successfully. It is boring
    # and I'm spending most of my time waiting while consuming resources
    # (memory and some CPU cycles). It's because the process is *blocking*.
    sleep(3)

    print "All done for", customer


def example1():
    # I do this all day long for our customers
    def developer_day(customers):
        for customer in customers:
            install_wordpress(customer)

    developer_day(["Bill", "Elon", "Steve", "Mark"])


def example2():
    import threading

    # The company grew. We now have many customers and I can't handle the
    # workload. We are now 5 developers doing exactly the same thing.
    def developers_day(customers):
        # But we now have to synchronize... a.k.a. bureaucracy
        lock = threading.Lock()

        def dev_day(id):
            print "Goodmorning from developer", id
            # Yuck - I hate locks...
            lock.acquire()
            while customers:
                customer = customers.pop(0)
                lock.release()
                # My Python is less readable
                install_wordpress(customer)
                lock.acquire()
            lock.release()
            print "Bye from developer", id

        # We go to work in the morning
        devs = [threading.Thread(target=dev_day, args=(i,)) for i in range(5)]
        [dev.start() for dev in devs]
        # We leave for the evening
        [dev.join() for dev in devs]

    # We now get more done in the same time but our dev process got more
    # complex. As we grew we spend more time managing queues than doing dev
    # work. We even had occasional deadlocks when processes got extremely
    # complex. The fact is that we are still mostly pressing buttons and
    # waiting but now we also spend some time in meetings.
    developers_day(["Customer %d" % i for i in xrange(15)])

# For years we thought this was all there was... We kept hiring more
# developers, more managers and buying servers. We were trying harder
# optimising processes and fire-fighting while getting mediocre performance in
# return. Till luckily one day our hosting company decided to increase their
# fees and we decided to switch to Twisted Ltd.!


def example3():
    from twisted.internet import reactor
    from twisted.internet import defer
    from twisted.internet import task

    # Twisted has a slightly different approach
    def schedule_install(customer):
        # They are calling us back when a Wordpress installation completes.
        # They connected the caller recognition system with our CRM and
        # we know exactly what a call is about and what has to be done next.

        # We now design processes of what has to happen on certain events.
        def schedule_install_wordpress():
            def on_done():
                print "Callback: Finished installation for", customer
            print "Scheduling: Installation for", customer
            return task.deferLater(reactor, 3, on_done)

        def all_done(_):
            print "All done for", customer

        # For each customer, we schedule these processes on the CRM and that
        # is all our chief-Twisted developer has to do
        d = schedule_install_wordpress()
        d.addCallback(all_done)

        return d

    # Yes, we don't need many developers anymore nor any synchronization.
    # ~~ Super-powered Twisted developer ~~
    def twisted_developer_day(customers):
        print "Goodmorning from Twisted developer"

        # Here's what has to be done today
        work = [schedule_install(customer) for customer in customers]
        # Turn off the lights when done
        join = defer.DeferredList(work)
        join.addCallback(lambda _: reactor.stop())

        print "Bye from Twisted developer!"

    # Even his day is particularly short!
    twisted_developer_day(["Customer %d" % i for i in xrange(15)])

    # Reactor, our secretary uses the CRM and follows-up on events!
    reactor.run()


def example4():
    from twisted.internet import reactor
    from twisted.internet import defer
    from twisted.internet import task

    # Twisted gave us utilities that make our code way more readable!
    @defer.inlineCallbacks
    def inline_install(customer):
        print "Scheduling: Installation for", customer
        yield task.deferLater(reactor, 3, lambda: None)
        print "Callback: Finished installation for", customer

        print "All done for", customer

    # Still no developers or synchronization.
    # ~~ Super-powered Twisted developer ~~
    def twisted_developer_day(customers):
        print "Goodmorning from Twisted developer"
        work = [inline_install(customer) for customer in customers]
        join = defer.DeferredList(work)
        join.addCallback(lambda _: reactor.stop())
        print "Bye from Twisted developer!"

    twisted_developer_day(["Customer %d" % i for i in xrange(15)])
    reactor.run()


def example5():
    from twisted.internet import reactor
    from twisted.internet import defer
    from twisted.internet import task

    @defer.inlineCallbacks
    def inline_install(customer):
        print "Scheduling: Installation for", customer
        yield task.deferLater(reactor, 3, lambda: None)
        print "Callback: Finished installation for", customer
        print "All done for", customer

    # The new "problem" is that we have to manage all this concurrency to
    # avoid causing problems to others, but this is a nice problem to have.
    def twisted_developer_day(customers):
        print "Goodmorning from Twisted developer"
        work = (inline_install(customer) for customer in customers)

        # We use the Cooperator mechanism to make the secretary not service
        # more than 5 customers simultaneously.
        coop = task.Cooperator()
        join = defer.DeferredList([coop.coiterate(work) for i in xrange(5)])

        join.addCallback(lambda _: reactor.stop())
        print "Bye from Twisted developer!"

    twisted_developer_day(["Customer %d" % i for i in xrange(15)])

    reactor.run()

# We are now more lean than ever, our customers happy, our hosting bills
# ridiculously low and our performance stellar.

# ~*~ THE END ~*~

if __name__ == "__main__":
    # Parsing arguments
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('example', metavar='example', type=int, nargs='?',
                        choices=xrange(6), help='example to run')
    args = parser.parse_args()

    if args.example is not None:
        import time
        # I know which example to run
        print "------ Running example", args.example, "------"
        start = time.time()
        # Run the appropriate local function
        locals()["example%d" % args.example]()
        end = time.time()
        print "* Elapsed time: %3.2f seconds" % (end - start)
    else:
        # I don't have arguments, so I run experiments 1-5 one after
        # the other
        import sys
        import subprocess
        [subprocess.call([sys.argv[0], str(i)]) for i in xrange(1, 6)]
