#!/usr/bin/env python

import os
import math
import sys
import tenjin
from tenjin.helpers import to_str, escape
from random import choice, randint

# To void linting error. Those two
# are used within engine.render()
(to_str, escape)

engine = tenjin.Engine()

tocreate = int(sys.argv[1])
index_contains = 30

locations = filter(None, [line.strip() for line in open("locations.txt")])
titles = filter(None, [line.strip() for line in open("titles.txt")])
descriptions = filter(None, [line.strip() for line in
                             open("descriptions.txt")])

create_sentence = lambda x: " ".join([choice(x) for i in
                                      xrange(0, randint(1, 10))])

if not os.path.exists('properties'):
    os.mkdir('properties')

items = []
for t in xrange(0, tocreate):
    location = choice(locations)
    title = create_sentence(titles)
    description = "\r\n".join([create_sentence(descriptions) for i in
                               xrange(0, randint(1, 5))])
    price = str(float(randint(12000, 40000))/100)
    image = "../images/i%02d.jpg" % randint(0, 17)

    item = {
        "description": description,
        "title": title,
        "price": price,
        "address": location,
        "image": image,
        "link": "property_%06d.html" % len(items)
    }
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
