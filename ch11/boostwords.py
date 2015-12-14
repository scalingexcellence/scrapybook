from pyspark.context import SparkConf, SparkContext, RDD
from pyspark.streaming import StreamingContext
from operator import add
from pprint import pformat

import unittest
import json
import sys
import time


def add_tuples(acc, i):
    return tuple(map(add, acc, i))

def preprocess(raw_data):
    def item_to_keywords_list(item):
        words = set(item['title'][0].split())
        return [(k.lower(), (item['price'][0], 1)) for k in words]

    return (
        raw_data.map(lambda line: json.loads(line))
        .flatMap(item_to_keywords_list)
        .reduceByKey(add_tuples)
    )


def to_shifts(word_prices):
    if word_prices.isEmpty():
        return word_prices

    (sum0, cnt0) = word_prices.values().reduce(add_tuples)
    avg0 = sum0 / cnt0

    def calculate_shift((isum, icnt)):
        if cnt0 == icnt:
            return 1.0
        else:
            avg_with = isum / icnt
            avg_without = (sum0 - isum) / (cnt0 - icnt)
            return (avg_with - avg_without) / avg0

    return word_prices.mapValues(calculate_shift)


class NonStreamTestCase(unittest.TestCase):

    def test_one_line_preprocess(self):
        lines = [
            '{"title": ["Split Business Split"], "price": [1.0]}',
        ]

        word_prices_rdd = preprocess(sc.parallelize(lines, 1))

        word_prices = dict(word_prices_rdd.collect())

        self.assertEqual(2, len(word_prices))
        self.assertAlmostEqual(1, word_prices['business'][0])
        self.assertAlmostEqual(1, word_prices['split'][0])
        self.assertAlmostEqual(1, word_prices['business'][1])
        self.assertAlmostEqual(1, word_prices['split'][1])

    def test_two_line_preprocess(self):
        lines = [
            '{"title": ["Split Business Split"], "price": [1.0]}',
            '{"title": ["Need business"], "price": [2.0]}',
        ]

        word_prices_rdd = preprocess(sc.parallelize(lines, 1))

        word_prices = dict(word_prices_rdd.collect())

        self.assertEqual(3, len(word_prices))
        self.assertAlmostEqual(2, word_prices['need'][0])
        self.assertAlmostEqual(3, word_prices['business'][0])
        self.assertAlmostEqual(1, word_prices['split'][0])
        self.assertAlmostEqual(1, word_prices['need'][1])
        self.assertAlmostEqual(2, word_prices['business'][1])
        self.assertAlmostEqual(1, word_prices['split'][1])

    def test_one_line_shifts(self):
        lines = [
            '{"title": ["Split Business Split"], "price": [1.0]}',
        ]

        word_prices = preprocess(sc.parallelize(lines, 1))

        shiftsRdd = to_shifts(word_prices)

        shifts = dict(shiftsRdd.collect())

        self.assertEqual(2, len(shifts))
        self.assertAlmostEqual(0.0, shifts['business'])
        self.assertAlmostEqual(0.0, shifts['split'])

    def test_two_line_shifts(self):
        lines = [
            '{"title": ["Split Business Split"], "price": [1.0]}',
            '{"title": ["Need business"], "price": [2.0]}',
        ]

        word_prices = preprocess(sc.parallelize(lines, 1))

        shiftsRdd = to_shifts(word_prices)

        shifts = dict(shiftsRdd.collect())

        self.assertEqual(3, len(shifts))
        self.assertAlmostEqual(0.44444444, shifts['need'])
        self.assertAlmostEqual(0.0, shifts['business'])
        self.assertAlmostEqual(-0.44444444, shifts['split'])


class BaseStreamingTestCase(unittest.TestCase):
    """ From https://github.com/apache/spark/blob/
    master/python/pyspark/streaming/tests.py """

    timeout = 10  # seconds
    duration = .5

    def setUp(self):
        self.ssc = StreamingContext(sc, self.duration)

    def tearDown(self):
        self.ssc.stop(False)

    def wait_for(self, result, n):
        start_time = time.time()
        while len(result) < n and time.time() - start_time < self.timeout:
            time.sleep(0.01)
        if len(result) < n:
            print("timeout after", self.timeout)

    def _collect(self, dstream, n):
        result = []

        def get_output(_, rdd):
            if rdd and len(result) < n:
                r = rdd.collect()
                if r:
                    result.append(r)

        dstream.foreachRDD(get_output)

        self.ssc.start()
        self.wait_for(result, n)
        return result


def update_state_function(new_values, prev):
    return reduce(add_tuples, new_values, prev or (0, 0))


class SmokeStreaming(BaseStreamingTestCase):

    def test_map(self):
        """Test streaming operation for the use case above"""

        input = [
            ['{"title": ["Split Business Split"], "price": [1.0]}'],
            ['{"title": ["Need business"], "price": [2.0]}'],
        ]

        input = [sc.parallelize(d, 1) for d in input]

        raw_data = self.ssc.queueStream(input)

        word_prices = preprocess(raw_data)

        running_word_prices = word_prices.updateStateByKey(update_state_function)

        shifts = running_word_prices.transform(to_shifts)

        output = self._collect(shifts, 2)

        # The first RDD is trivial
        shifts = dict(output.pop(0))

        self.assertEqual(2, len(shifts))
        self.assertAlmostEqual(0.0, shifts['business'])
        self.assertAlmostEqual(0.0, shifts['split'])

        # The second RDD includes the values from the first because of
        # updateStateByKey().
        shifts = dict(output.pop(0))

        self.assertEqual(3, len(shifts))
        self.assertAlmostEqual(0.44444444, shifts['need'])
        self.assertAlmostEqual(0.0, shifts['business'])
        self.assertAlmostEqual(-0.44444444, shifts['split'])

def print_shifts(shifts):
    print("\033c" +
          pformat(
              shifts.takeOrdered(5, lambda (k, v): -v) +
              ['...'] +
              list(reversed(shifts.takeOrdered(5, lambda (k, v): v)))
          )
    )
    
def main(ssc, args):
    if len(args) < 2:
        print "usage: spark-submit book/ch11/boostwords.py file:///root/items"
        sys.exit()

    # Monitor the files and give us a DStream of term-price pairs
    raw_data = ssc.textFileStream(args[1])
    word_prices = preprocess(raw_data)
    
    # Update the counters using Spark's updateStateByKey
    running_word_prices = word_prices.updateStateByKey(update_state_function)

    # Calculate shifts out of the counters
    shifts = running_word_prices.transform(to_shifts)

    # Print the results
    shifts.foreachRDD(print_shifts)
            
if __name__ == "__main__":

    if len(sys.argv) >= 2 and sys.argv[1] == "test":
        # Run the tests
        del sys.argv[1]

        conf = SparkConf().set("spark.default.parallelism", 1)

        sc = SparkContext(appName='unit_test', conf=conf)

        sc.setLogLevel("WARN")

        sc.setCheckpointDir("/tmp")

        unittest.main()

        sc.stop()

    else:
        # Run the main()
        sc = SparkContext(appName="BoostWords")

        sc.setLogLevel("WARN")

        ssc = StreamingContext(sc, 5)

        ssc.checkpoint("checkpoint")
        
        main(ssc, sys.argv)

        # Start the engine
        ssc.start()

        ssc.awaitTermination()
