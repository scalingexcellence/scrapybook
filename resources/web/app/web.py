#!/usr/bin/env python

import re
import json
import random

from zope.interface import Interface, Attribute, implements
from twisted.python.components import registerAdapter
from twisted.internet.task import deferLater
from twisted.web.resource import Resource
from twisted.web.util import redirectTo
from twisted.web.server import Session
from twisted.internet import reactor
from twisted.web.static import File
from twisted.web import server

from model import Model
from view import View


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


class Dummy(object):

    def getfloat(self, str, default):
        return default

    def getint(self, str, default):
        return default


class Api(BaseResource):

    def __init__(self, settings=Dummy()):
        delay = settings.getfloat('SPEED_API_T_RESPONSE',
                                  settings.getfloat('SPEED_T_RESPONSE', 3))
        BaseResource.__init__(self, delay)

    def _delayedRender(self, request):
        text = self.get_if(request, 'text', '', str)
        request.write(json.dumps({"translation": "api-t-%s" % "".join(text)}))
        request.finish()


class Index(BaseResource):

    def __init__(self, settings=Dummy()):
        delay = settings.getfloat('SPEED_INDEX_T_RESPONSE',
                                  settings.getfloat('SPEED_T_RESPONSE', 0.5))
        BaseResource.__init__(self, delay)
        self.details_per_index = settings.getint(
            'SPEED_DETAILS_PER_INDEX_PAGE', 20)
        self.items_per_page = settings.getint('SPEED_ITEMS_PER_DETAIL', 1)
        self.limit = settings.getint('SPEED_TOTAL_ITEMS', 1000)
        self.index_lookahead = settings.getint('SPEED_INDEX_POINTAHEAD', 1)

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
                    request.write('<li><a class="item" href="detail'
                                  '?id0=%d">item %s</a></li>' % (id, srange))

            request.write('</ul>')

            for i in xrange(self.index_lookahead):
                if (p+i) < max_pages:
                    request.write('<a class="nav" href="index?p=%d">next</a> '
                                  % (p+i+1))

        request.finish()


class Detail(BaseResource):

    def __init__(self, settings=Dummy()):
        delay = settings.getfloat('SPEED_DETAIL_T_RESPONSE',
                                  settings.getfloat('SPEED_T_RESPONSE', 1))
        BaseResource.__init__(self, delay)
        self.items_per_page = settings.getint('SPEED_ITEMS_PER_DETAIL', 1)
        self.limit = settings.getint('SPEED_TOTAL_ITEMS', 1000)
        self.garbage_size = settings.getint('SPEED_DETAIL_EXTRA_SIZE', 0)

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
        request.write('<!--')
        request.write("i" * self.garbage_size)
        request.write('-->')
        request.finish()


class Benchmark(Resource):

    def __init__(self):
        Resource.__init__(self)

        self.putChild("api", Api())
        self.putChild("index", Index())
        self.putChild("detail", Detail())

    def getChild(self, name, request):
        return self

    def render_GET(self, request):
        return ('Resource not found. Try: '
                '<a href="benchmark/api?text=foo">api</a>, '
                '<a href="benchmark/index?p=1">index</a>, '
                '<a href="benchmark/detail?id0=1">detail</a>')


class ILoginGate(Interface):
    nonce = Attribute("random nonce")
    logged_in = Attribute("true if successfully logged in")


class LoginGate(object):
    implements(ILoginGate)

    def __init__(self, session):
        self.nonce = str(random.random())
        self.logged_in = False


registerAdapter(LoginGate, Session, ILoginGate)


class Dynamic(Resource):

    def __init__(self):
        Resource.__init__(self)

    def getChild(self, name, request):
        return self

    def render_GET(self, request):
        session = request.getSession()
        tsesion = ILoginGate(session)

        try:
            if request.path == "/dynamic":
                return View.render_form(tsesion.nonce)

            elif request.path == "/dynamic/gated":
                if not tsesion.logged_in:
                    return redirectTo("/dynamic/error", request)

                return View.render_gated()
        except:
            pass

        session.expire()
        return View.render_error()

    def render_POST(self, request):
        session = request.getSession()
        tsesion = ILoginGate(session)
        location = "/dynamic/error"

        try:
            if request.path not in ["/dynamic/nonce-login", "/dynamic/login"]:
                raise Exception('unsupported login type')

            if request.path == "/dynamic/nonce-login":
                nonce = request.args.get('nonce', [''])[0]

                if tsesion.nonce != nonce:
                    session.expire()
                    raise Exception('invalid nonce')

            if (request.args.get('user', [''])[0] != 'user' or
                    request.args.get('pass', [''])[0] != 'pass'):
                if session:
                    session.expire()
                raise Exception('invalid user/pass')

            tsesion.logged_in = True
            location = "/dynamic/gated"

        except:
            pass

        return redirectTo(location, request)


class Properties(BaseResource):

    def __init__(self):
        # 250 ms default delay
        BaseResource.__init__(self, 0.25)

        self.model = Model()
        self.properties = 50000
        self.per_index = 30

    def _delayedRender(self, request):
        try:
            properties, per_index = self.properties, self.per_index

            if request.path == "/properties/api.json":
                items = []
                for i in xrange(30):
                    item = self.model.get_item(i)
                    items.append({'id': i, "title": item['title']})

                request.setHeader("content-type", "application/json")
                request.write(json.dumps(items))

            elif request.path.startswith("/properties/index_"):
                m = re.search(r'.*_(\d+)', request.path)
                if not m:
                    raise Exception('expected number')

                page = int(m.group(1))

                # Divide with roundup
                indices = (properties + per_index - 1) / per_index
                if page >= indices:
                    raise Exception('invalid index number')

                np = "index_%05d.html" % (page+1)

                start = per_index * page
                end = min(per_index * (page + 1), properties)

                index = {
                    'page': page,
                    'nextp': None if page >= (indices-1) else np,
                    'items': self.model.get_items(xrange(start, end))
                }

                request.write(View.render_index(index))

            elif request.path.startswith("/properties/property_"):
                m = re.search(r'.*_(\d+)', request.path)
                if not m:
                    raise Exception('expected number')

                pid = int(m.group(1))

                if pid >= properties:
                    raise Exception('invalid property number')

                item = self.model.get_item(pid)

                request.write(View.render_property(item))
            else:
                raise Exception('unknown page')
                
        except:
            request.write('can\'t find page. sorry')

        request.finish()


class Root(Resource):
    def __init__(self):
        Resource.__init__(self)
        self.putChild("benchmark", Benchmark())
        self.putChild("properties", Properties())
        self.putChild("images", File('images'))
        self.putChild("dynamic", Dynamic())

    def getChild(self, name, request):
        return self

    def render_GET(self, request):
        return ('Resource not found. Try: '
                '<a href="properties/index_00000.html">properties</a> '
                '<a href="images">images</a>, '
                '<a href="dynamic">dynamic</a>, '
                '<a href="benchmark">benchmark</a> ')

if __name__ == '__main__':

    site = server.Site(Root())

    reactor.listenTCP(9312, site)

    reactor.run()
