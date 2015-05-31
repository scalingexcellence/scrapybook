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
#    'properties.pipelines.redis_cache.RedisCache': 200,
    'properties.pipelines.geo.GeoPipeline': 300,
#    'properties.pipelines.computation.MultiThreads': 400,
#    'properties.pipelines.legacy.Pricing': 500,
    'properties.pipelines.mysql.MysqlWriter': 600,
    'properties.pipelines.es.EsWriter': 700,
}

import os
REDIS_PIPELINE_URL = os.environ.get('REDIS_PIPELINE_URL', 'redis://192.168.59.103:6379')
MYSQL_PIPELINE_URL = os.environ.get('MYSQL_PIPELINE_URL', 'mysql://root:pass@192.168.59.103/properties')
ES_PIPELINE_URL = os.environ.get('ES_PIPELINE_URL', 'http://192.168.59.103:9200/properties/property')

#CLOSESPIDER_ITEMCOUNT = 900
LOGSTATS_INTERVAL = 2
LOG_LEVEL = "INFO"
