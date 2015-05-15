from MySQLdb.cursors import DictCursor

from twisted.enterprise import adbapi
from scrapy.xlib.pydispatch import dispatcher
from scrapy import log
from scrapy import signals

class MysqlWriter(object):

    @classmethod
    def from_crawler(cls, crawler):
        # Get redis URL
        mysql_url = crawler.settings.get('MYSQL_PIPELINE_URL', None)
        
        # If doesn't exist, disable
        if not mysql_url:
            raise NotConfigured
            
        return cls(crawler, mysql_url)
        
    def __init__(self, crawler, mysql_url):
        self.mysql_url = mysql_url
        self.crawler = crawler
        
        conn_kwargs = MysqlWriter.parse_mysql_url(mysql_url)

        self.dbpool = adbapi.ConnectionPool('MySQLdb',
            charset='utf8',
            use_unicode=True,
            cursorclass=DictCursor,
            **conn_kwargs
        )
        
        # Close the database connection when you receive the "spider closed" signal
        crawler.signals.connect(self.dbpool.close, signal=signals.spider_closed)
    
    def process_item(self, item, spider):
        def do_replace(tx):
            result = tx.execute(
                """REPLACE INTO `properties` (`url`,`title`,`price`,`description`) VALUES (%s,%s,%s,%s)""",
                (item["url"][0][:100], item["title"][0][:30], item["price"][0], item["description"][0].replace("\r\n", " ")[:30])
            )
        
        d = self.dbpool.runInteraction(do_replace)
        d.addErrback(log.err)
        d.addBoth(lambda _: item)
        return d

    @staticmethod
    def parse_mysql_url(mysql_url):
        import dj_database_url
        
        params = dj_database_url.parse(mysql_url)
        
        conn_kwargs = {}
        conn_kwargs['host'] = params['HOST']
        conn_kwargs['user'] = params['USER']
        conn_kwargs['passwd'] = params['PASSWORD']
        conn_kwargs['db'] = params['NAME']
        conn_kwargs['port'] = params['PORT']

        # Remove items with empty values
        conn_kwargs = dict((k, v) for k, v in conn_kwargs.iteritems() if v)
        
        return conn_kwargs
