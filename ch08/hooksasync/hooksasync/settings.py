# Scrapy settings for hooksasync project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'hooksasync'

SPIDER_MODULES = ['hooksasync.spiders']
NEWSPIDER_MODULE = 'hooksasync.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'hooksasync (+http://www.yourdomain.com)'

# Extensions orders are not as important as middleware orders though, and they are typically
# irrelevant, ie. it doesn't matter in which order the extensions are loaded because they
# don't depend on each other.
EXTENSIONS             = { 'hooksasync.extensions.HooksasyncExtension'           : 100 }
DOWNLOADER_MIDDLEWARES = { 'hooksasync.extensions.HooksasyncDownloaderMiddleware': 100 }
SPIDER_MIDDLEWARES     = { 'hooksasync.extensions.HooksasyncSpiderMiddleware'    : 100 }
ITEM_PIPELINES         = { 'hooksasync.extensions.HooksasyncPipeline'            : 100 }

#CONCURRENT_ITEMS = 1
#CONCURRENT_REQUESTS = 1