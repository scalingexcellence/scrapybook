#!/usr/bin/env python

from model import Model

import os
import sys
import math
import tenjin
from tenjin.helpers import to_str, escape

# To void linting error. Those two
# are used within engine.render()
(to_str, escape)

tocreate = int(sys.argv[1])
index_contains = 30


if not os.path.exists('properties'):
    os.mkdir('properties')

engine = tenjin.Engine()
model = Model()

items = []
for t in xrange(0, tocreate):
    item = model.get_item(t)
    items.append(item)

    f = open("properties/property_%06d.html" % t, "w")
    f.write(engine.render('page.pyhtml', {'item': item}))
    f.close()

indices = int(math.ceil(float(tocreate)/index_contains))
for page in xrange(0, indices):
    nextp = None if page == (indices-1) else ("index_%05d.html" % (page+1))
    its = items[index_contains*page: min(index_contains*(page+1), tocreate)]
    f = open("properties/index_%05d.html" % page, "w")
    f.write(engine.render('index.pyhtml',
                          {'page': page, 'nextp': nextp, 'its': its}))
    f.close()
