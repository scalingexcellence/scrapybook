# Scrapy settings for properties project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'properties'

SPIDER_MODULES = ['properties.spiders']
NEWSPIDER_MODULE = 'properties.spiders'

# Crawl responsibly by identifying yourself (and your website) on
# the user-agent
#USER_AGENT = 'properties (+http://www.yourdomain.com)'

ITEM_PIPELINES = {
    'properties.pipelines.tidyup.TidyUp': 100,
    'properties.pipelines.redis.RedisCache': 300,    
    'properties.pipelines.geo.GeoPipeline': 400,
    'properties.pipelines.computation.UsingBlocking': 500,
    'properties.pipelines.legacy.Pricing': 600,
    'properties.pipelines.mysql.MysqlWriter': 700,
    'properties.pipelines.es.EsWriter': 800,
}

EXTENSIONS = {'properties.latencies.Latencies': 500, }
LATENCIES_INTERVAL = 5

import os

REDIS_DEFAULT_URL = 'redis://192.168.59.103:6379'
REDIS_PIPELINE_URL = os.environ.get('REDIS_PIPELINE_URL', REDIS_DEFAULT_URL)

MYSQL_DEFAULT_URL = 'mysql://root:pass@192.168.59.103/properties'
MYSQL_PIPELINE_URL = os.environ.get('MYSQL_PIPELINE_URL', MYSQL_DEFAULT_URL)

ES_DEFAULT_URL = 'http://192.168.59.103:9200/properties/property'
ES_PIPELINE_URL = os.environ.get('ES_PIPELINE_URL', ES_DEFAULT_URL)

#CLOSESPIDER_ITEMCOUNT = 900
LOG_LEVEL = "INFO"
