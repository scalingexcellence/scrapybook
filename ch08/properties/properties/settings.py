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
}

EXTENSIONS = {'properties.latencies.Latencies': 500}
LATENCIES_INTERVAL = 5

COMMANDS_MODULE = 'properties.hi'

# Disable S3
AWS_ACCESS_KEY_ID = ""
AWS_SECRET_ACCESS_KEY = ""
