#!/usr/bin/env python

import tenjin
from tenjin.helpers import *
from tenjin.html import *
from random import choice, uniform

engine = tenjin.Engine()

domain = "http://scrapybook.s3-website-us-east-1.amazonaws.com/"

locations = filter(None, [line.strip() for line in open("locations.txt")])

location = choice(locations)

price = uniform(120, 400)
image = "a%d.jpg" % uniform(2,2)

item = {
	"description" : "Great ROOM SHARE AVAILABLE - sharing the room with a male. \r\nIn the heart of Fulham ZONE 2 \r\nClose to the Parsons Green Park & all local Amenities. \r\nALL bills are FULLY inclusive, Including UNLIMITED internet. \r\nWE ARE NOT AN AGENCY, NEVER CHARGE ANY FEES! \r\nVery Popular and at a Great DEAL!!!!",
	"title" : "Male room share available Now - Twin Room - Fulham",
	"breadcrumbs" : [ "United Kingdom", location ],
	"price" : price,
	"address" : location,
	"image" : domain + "images/" + image
}

html = engine.render('page.pyhtml', {'item':item} )
print(html)





