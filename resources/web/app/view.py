#!/usr/bin/env python
# -*- coding: utf-8 -*-


class View(object):
    """Yaick! This class hurts my eyes... but it's fast and simple
    """
    @staticmethod
    def render_form(uid):
        return """
<!DOCTYPE html>
<head>
<meta charset="utf-8">
<title>Welcome</title>
</head>
<body>
<h1>Welcome, please login</h1>
<form method="post" action="/dynamic/nonce-login">
<p><input type="text" name="user" value="" placeholder="Username"></p>
<p><input type="password" name="pass" value="" placeholder="Password"></p>
<p class="submit"><input type="submit" name="submit" value="Login"></p>
<input type="hidden" name="nonce" value="%s" />
</form>
</body>
</html>
""" % uid

    @staticmethod
    def render_error():
        return """
<!DOCTYPE html><head><meta charset="utf-8">
<title>Error</title></head><body><h1>Page not found</h1>
<p>Return to <a href="/dynamic">login</a>
</body></html>"""

    @staticmethod
    def render_gated():
        return """
<!DOCTYPE html>
<head>
<meta charset="utf-8">
<title>Congratulations</title>
</head>
<body>
<h1>Here are your links</h1>
<ul class="links">
<li><a href="../properties/property_000000.html" itemprop="url">link1</a></li>
<li><a href="../properties/property_000001.html" itemprop="url">link2</a></li>
<li><a href="../properties/property_000002.html" itemprop="url">link3</a></li>
</ul>
</body>
</html>
"""

    @staticmethod
    def render_index(idx):
        parts = []

        parts.append("""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Scrapy Book Tutorial Example</title>
<style type="text/css">
a {text-decoration:none;}
.listing-description { font-size: 7px; display:block; }
</style>
</head>
<body>
<h1>Page %d</h1>
<ul>
""" % idx['page'])

        for item in idx['items']:
            parts.append("""
<li class="listing-maxi" itemscope itemtype="http://schema.org/Product">
  <a class="listing-link" itemprop="url" href="%s">
  <img itemprop="image" src="%s" width="15" height="15" alt="thumb" />
  <span class="listing-title" itemprop="name">%s</span>, price:
  <span itemprop="price">£%spw</span>
  location: <span itemscope itemtype="http://schema.org/Place">
  <span>%s</span></span>
  <span class="listing-description" itemprop="description">%s</span>
  </a>
</li>
""" % (
                item['link'],
                item['image'],
                item['title'],
                item['price'],
                item['address'],
                item['description']
                ))

        parts.append("""</ul>""")

        if idx['nextp']:
            parts.append("""
<ul><li class="next"><a href="%s" rel="nofollow">next</a></li></ul>
""" % idx['nextp'])

        parts.append("""</body></html>""")

        return ''.join(parts)

    @staticmethod
    def render_property(item):
        return """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>Scrapy Book Tutorial Example</title>
</head>
<body itemscope itemtype="http://schema.org/Product">
<h1 itemprop="name" class="space-mbs">%s</h1>
<strong class="ad-price txt-xlarge txt-emphasis" itemprop="price">
£%spw</strong>
<p itemprop="description">%s</p>
<img src="%s" alt="image" itemprop="image" />
<p itemscope itemtype="http://schema.org/Place">%s</p>
</body>
</html>
""" % (
            item['title'],
            item["price"],
            item['description'],
            item['image'],
            item['address']
            )
