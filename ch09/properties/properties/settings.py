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
    'properties.pipelines.es.EsWriter': 800,
    #'properties.pipelines.geo.GeoPipeline': 400,
    'properties.pipelines.geo2.GeoPipeline': 400,
    'properties.pipelines.mysql.MysqlWriter': 700,
    'properties.pipelines.redis.RedisCache': 300,
    'properties.pipelines.computation.UsingBlocking': 500,
    'properties.pipelines.legacy.Pricing': 600,
}

EXTENSIONS = {'properties.latencies.Latencies': 500, }
LATENCIES_INTERVAL = 5

ES_PIPELINE_URL = 'http://es:9200/properties/property/'

MYSQL_PIPELINE_URL = 'mysql://root:pass@mysql/properties'

REDIS_PIPELINE_URL = 'redis://redis:6379'

LOG_LEVEL = "INFO"

# Disable S3
AWS_ACCESS_KEY_ID = ""
AWS_SECRET_ACCESS_KEY = ""
