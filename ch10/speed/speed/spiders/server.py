#!/usr/bin/env python

import json

from twisted.internet.task import deferLater
from twisted.web.resource import Resource
from twisted.internet import reactor
from twisted.web import server


class BaseResource(Resource):
    isLeaf = True

    def __init__(self, delay):
        Resource.__init__(self)
        self.delay = delay

    @staticmethod
    def get_if(request, k, default, cls):
        try:
            return cls(request.args[k][0])
        except:
            return default

    def render_GET(self, request):
        # https://twistedmatrix.com/documents/13.0.0/web/howto/
        #web-in-60/asynchronous-deferred.html
        d = deferLater(reactor, self.delay, lambda: request)
        d.addCallback(self._delayedRender)
        return server.NOT_DONE_YET

    render_POST = render_GET


class Api(BaseResource):

    def __init__(self, settings):
        delay = settings.getfloat('SPEED_API_T_RESPONSE',
                                  settings.getfloat('SPEED_T_RESPONSE', 3))
        BaseResource.__init__(self, delay)

    def _delayedRender(self, request):
        text = self.get_if(request, 'text', '', str)
        request.write(json.dumps({"translation": "api-t-%s" % "".join(text)}))
        request.finish()


class Index(BaseResource):

    def __init__(self, settings):
        delay = settings.getfloat('SPEED_INDEX_T_RESPONSE',
                                  settings.getfloat('SPEED_T_RESPONSE', 0.5))
        BaseResource.__init__(self, delay)
        self.details_per_index = settings.getint(
            'SPEED_DETAILS_PER_INDEX_PAGE', 20)
        self.items_per_page = settings.getint('SPEED_ITEMS_PER_DETAIL', 1)
        self.limit = settings.getint('SPEED_TOTAL_ITEMS', 1000)
        self.index_lookahead = settings.getint('SPEED_INDEX_POINTAHEAD', 4)

    def _delayedRender(self, request):
        p = self.get_if(request, 'p', 1, int)

        page_worth = self.details_per_index * self.items_per_page
        # ...divide with roundup
        max_pages = (self.limit + page_worth - 1) / page_worth

        if p >= 1 and p <= max_pages:
            base = (p-1) * self.details_per_index
            request.write('<ul>')
            for i in xrange(self.details_per_index):
                id = ((base+i)*self.items_per_page)+1
                if id <= self.limit:
                    ids = [id, min(id + self.items_per_page - 1, self.limit)]
                    irange = sorted(list(set(ids)))
                    srange = "-".join([str(i) for i in irange])
                    request.write('<li><a class="item" href="../detail'
                                  '?id0=%d">item %s</a></li>' % (id, srange))

            request.write('</ul>')

            for i in xrange(self.index_lookahead):
                if (p+i) < max_pages:
                    request.write('<a class="nav" href="index?p=%d">next</a> '
                                  % (p+i+1))

        request.finish()


class Detail(BaseResource):

    def __init__(self, settings):
        delay = settings.getfloat('SPEED_DETAIL_T_RESPONSE',
                                  settings.getfloat('SPEED_T_RESPONSE', 1))
        BaseResource.__init__(self, delay)
        self.items_per_page = settings.getint('SPEED_ITEMS_PER_DETAIL', 1)
        self.limit = settings.getint('SPEED_TOTAL_ITEMS', 1000)

    def _delayedRender(self, request):
        id0 = self.get_if(request, 'id0', 1, int)
        request.write('<ul>')
        for idx in xrange(id0, min(id0+self.items_per_page, self.limit+1)):
            request.write('<li>')
            request.write('<h3>I\'m %d</h3>' % idx)
            request.write('<div class="info">useful info for id: %d</div>'
                          % idx)
            request.write('</li>')
        request.write('</ul>')
        request.finish()


class Root(Resource):
    def __init__(self, settings):
        Resource.__init__(self)
        self.putChild("api", Api(settings))
        self.putChild("index", Index(settings))
        self.putChild("detail", Detail(settings))

    def getChild(self, name, request):
        return self

    def render_GET(self, request):
        return 'Resource not found. Try: <a href="api?text=foo">api</a>, <a '
        'href="index?p=1">index</a>, <a href="detail?id0=1">detail</a>'


class SimpleServer(object):
    def __init__(self, port, settings):
        self.porthandler = reactor.listenTCP(port, server.Site(Root(settings)))

    def close(self):
        self.porthandler.stopListening()
