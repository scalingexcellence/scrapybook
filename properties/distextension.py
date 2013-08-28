from scrapy import signals
from scrapy.exceptions import NotConfigured
from w3lib.url import file_uri_to_path

import requests
import pickle
import socket
import subprocess
import random

links_extracted = object()


class BatchToScrapyd(object):
    def __init__(self, fworkers, project, batch_size, host, db, collection):
        self.fworkers = fworkers
        self.project = project
        self.batch_size = batch_size
        self.host = host
        self.db = db
        self.collection = collection

        try:
            self.workers = filter(
                None,
                [line.strip() for line in open(fworkers)]
            )
        except IOError:
            self.workers = ["localhost"]

        self.batch = []

    @classmethod
    def from_crawler(cls, crawler):
        # instantiate the extension object
        host = socket.gethostbyname(socket.gethostname())
        ext = cls(
            crawler.settings.get('DIST_WORKERS', "workers.txt"),
            crawler.settings.get('BOT_NAME'),
            crawler.settings.getint('DIST_BATCH_SIZE', 1000),
            crawler.settings.get('DIST_MONGO_HOST', host),
            crawler.settings.get('DIST_MONGO_DB'),
            crawler.settings.get('DIST_MONGO_COLLECTION')
        )

        # connect the extension object to signals
        crawler.signals.connect(ext.send_batch, signal=signals.spider_closed)
        crawler.signals.connect(ext.add_to_batch, signal=links_extracted)

        # return the extension object
        return ext

    def add_to_batch(self, spider, urls):
        self.batch += urls
        if len(self.batch) >= self.batch_size:
            self.send_batch(spider)

    def send_batch(self, spider):
        if not self.batch:
            return

        if not self.db or not self.collection or not self.workers:
            spider.log("BatchToScrapyd: DIST_MONGO_DB or " +
                       "DIST_MONGO_COLLECTION not set " +
                       "OR '%s' file is empty" % self.fworkers)
        else:
            worker = random.choice(self.workers)
            requests.post("http://%s:6800/schedule.json" % worker, data={
                "project":    self.project,
                "spider":     spider.name.replace("-master", "-worker"),
                "url":        pickle.dumps(self.batch),
                "setting":  [
                    "MONGO_IMPORT_HOST=%s" % self.host,
                    "MONGO_IMPORT_DB=%s" % self.db,
                    "MONGO_IMPORT_COLLECTION=%s" % self.collection
                ]
            })
            print "BatchToScrapyd: Scheduled %d URLs on node %s" % (
                len(self.batch), worker)

        self.batch = []


class MongoImportOnFinish(object):

    def __init__(self, host, db, collection, feed):
        self.host = host
        self.db = db
        self.collection = collection
        self.feed = feed

    @classmethod
    def from_crawler(cls, crawler):
        # first check if the extension should be enabled and raise
        # NotConfigured otherwise
        if not all([
            crawler.settings.get('MONGO_IMPORT_DB'),
            crawler.settings.get('MONGO_IMPORT_COLLECTION')
        ]):
            raise NotConfigured

        # instantiate the extension object
        ext = cls(
            crawler.settings.get('MONGO_IMPORT_HOST', 'localhost'),
            crawler.settings.get('MONGO_IMPORT_DB'),
            crawler.settings.get('MONGO_IMPORT_COLLECTION'),
            crawler.settings.get('FEED_URI')
        )

        # connect the extension object to signals
        crawler.signals.connect(ext.mongoimport, signal=signals.spider_closed)

        # return the extension object
        return ext

    def mongoimport(self, spider):
        if not self.feed:
            spider.log("MongoImportOnFinish: Feed file not defined")
            return

        args = [
            'mongoimport',
            '--host', self.host,
            '--db', self.db,
            '--collection', self.collection,
            '--file', file_uri_to_path(self.feed)
        ]
        subprocess.call(args)
        spider.log(" ".join(args))
