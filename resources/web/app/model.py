#!/usr/bin/env python

import math
import unittest
import types

class Model(object):

    def __init__(self):
        self._locations = Model.from_file("locations.txt")
        self._titles = Model.from_file("titles.txt")
        self._descriptions = Model.from_file("descriptions.txt")
        gen = Generator(0xc0febabe)
        self._title_weights = gen.create_weights(self._titles)

    def get_item(self, i):
        return next(self.get_items([i]))
        
    def get_items(self, ids):
        for i in ids:
            gen = Generator(i+1)  # Avoid 0

            location = gen.choice(self._locations)
            title = gen.create_sentence(self._titles)
            description = gen.create_paragraph(self._descriptions)
            price = str(gen.rand_price(title, self._title_weights))
            image = "../images/i%02d.jpg" % gen.rand(17)

            yield {
                "description": description,
                "title": title,
                "price": price,
                "address": location,
                "image": image,
                "link": "property_%06d.html" % i
            }

    @staticmethod
    def from_file(file):
        return filter(None, [line.strip() for line in open(file)])


# Use this instead of rand because it will be the same no matter
# where/when it runs
class Generator(object):
    def __init__(self, seed):
        self._seed = seed

    def create_paragraph(self, options):
        num_lines = self.rand(4) + 1
        return "\r\n".join(
            [self.create_sentence(options) for i in xrange(num_lines)]
        )

    def create_sentence(self, options):
        num_words = self.rand(7) + 3
        return " ".join([self.choice(options) for i in xrange(0, num_words)])

    def choice(self, options):
        return options[self.rand(len(options))]

    def rand_price(self, title, weights):
        words = set(title.split(' '))
        boost = sum((weights[w] for w in words))
        # We don't accept boosts that yeield less than 30% of the price
        return round((1.0 + boost) * (700. + self.rand(600)), 2)

    def create_weights(self, titles):
        weights = {}
        quant = 980000
        var = 0.4
        for w in titles:
            r = self.rand(quant)
            v_norm = float(r) / quant
            weight = math.copysign(var * math.exp(- 100 * v_norm), r % 2 - 1)
            weights[w] = round(weight, 2)
        return weights

    def rand(self, maxv):
        # Numerical Recipes LCG
        self._seed = (1664525 * self._seed + 1013904223) % (1 << 32)
        return self._seed % maxv


class TestModel(unittest.TestCase):
    def setUp(self):
        self.model = Model()

    def test_create(self):
        expected = {
            'address': 'Angel, London',
            'description': 'equipped everyone itself',
            'image': '../images/i06.jpg',
            'link': 'property_000001.html',
            'price': '707.0',
            'title': 'own n top westminster residential electric click'
        }
        self.assertEqual(expected, self.model.get_item(1))

        expected = {
            'address': 'Angel, London',
            'description': 'from main quay hours lane original\r\nbetween en '
            'power selection comprises\r\nextremely ceilings facilities '
            'present ring natural availability together',
            'image': '../images/i00.jpg',
            'link': 'property_000323.html',
            'price': '1287.92',
            'title': 'sale congrats de'
        }
        self.assertEqual(expected, self.model.get_item(323))

    def test_bulk_crate(self):
        items = self.model.get_items(xrange(3))
        self.assertTrue(isinstance(items, types.GeneratorType))
        self.assertEqual('property_000000.html', next(items)['link'])
        self.assertEqual('property_000001.html', next(items)['link'])
        self.assertEqual('property_000002.html', next(items)['link'])
        with self.assertRaises(StopIteration):
            next(items)

if __name__ == '__main__':
    unittest.main()
