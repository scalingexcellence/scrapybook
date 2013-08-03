#!/usr/bin/env python

import tenjin, os, math, sys
from tenjin.helpers import *
from tenjin.html import *
from random import choice, randint

engine = tenjin.Engine()

tocreate = int(sys.argv[1])
index_contains = 50

locations = filter(None, [line.strip() for line in open("locations.txt")])
titles = filter(None, [line.strip() for line in open("titles.txt")])
descriptions = filter(None, [line.strip() for line in open("descriptions.txt")])

create_sentence = lambda x: " ".join([choice(x) for i in xrange(0,randint(1,10))])

if not os.path.exists('properties'):
    os.mkdir('properties')

for t in xrange(0,tocreate):
    location = choice(locations)
    title = create_sentence(titles)
    description = "\r\n".join([create_sentence(descriptions) for i in xrange(0,randint(1,5))])
    price = ", price: %d" % randint(120, 400)
    image = "images/i%02d.jpg" % randint(0,17)

    item = {
        "description" : description,
        "title" : title,
        "breadcrumbs" : [ location ],
        "price" : price,
        "address" : location,
        "image" : image
    }
    
    f = open("properties/property_%06d.html" % t, "w")
    f.write(engine.render('page.pyhtml', {'item':item} ))
    f.close()

indices = int(math.ceil(float(tocreate)/index_contains))
for page in xrange(0,indices):
    nextp = None if page == (indices-1) else ("index_%05d.html" % (page+1))
    links = [ "property_%06d.html" % t for t in xrange(index_contains*page, min(index_contains*(page+1), tocreate)) ]
    f = open("properties/index_%05d.html" % page, "w")
    f.write(engine.render('index.pyhtml', {'page':page, 'nextp':nextp, 'links': links} ))
    f.close()

