# -*- coding: utf-8 -*-

BOT_NAME = 'speed'

SPIDER_MODULES = ['speed.spiders']
NEWSPIDER_MODULE = 'speed.spiders'


#SPEED_PORT = 9312

ITEM_PIPELINES = {'speed.spiders.speed.DummyPipeline': 100}
EXTENSIONS = {'speed.spiders.speed.PrintCoreMetrics': 500}

# Disable S3
AWS_ACCESS_KEY_ID = ""
AWS_SECRET_ACCESS_KEY = ""

# Defaults for high performance
# See http://doc.scrapy.org/en/latest/topics/broad-crawls.html
LOG_LEVEL = "INFO"
COOKIES_ENABLED = False
RETRY_ENABLED = False
DOWNLOAD_TIMEOUT = 15
REDIRECT_ENABLED = False
REACTOR_THREADPOOL_MAXSIZE = 20
AJAXCRAWL_ENABLED = True
DEPTH_PRIORITY = 0
# We simplify the model by essentially
# disabling the per-IP limits.
CONCURRENT_REQUESTS_PER_DOMAIN = 1000000
# As long as you have one item per crawl
# it's better to have this set to 1
CONCURRENT_ITEMS = 1

# The most key Scrapy setting:
CONCURRENT_REQUESTS = 16

# Main simulation factors:
SPEED_TOTAL_ITEMS = 5000
SPEED_T_RESPONSE = 0.125

# *** Spider simulation settings ***
#SPEED_SPIDER_BLOCKING_DELAY = 0

# *** Pipeline control settings ***
#CONCURRENT_ITEMS = 100

# *** Pipeline simulation settings ***
#SPEED_PIPELINE_BLOCKING_DELAY = 0.2
#SPEED_PIPELINE_ASYNC_DELAY = 0.2
#SPEED_PIPELINE_API_VIA_DOWNLOADER = 0
#SPEED_PIPELINE_API_VIA_TREQ = 0

# *** Adjusting crawling style ***
#SPEED_INDEX_POINTAHEAD=1
#SPEED_INDEX_HIGHER_PRIORITY = False
#SPEED_START_REQUESTS_STYLE = 'Force' # or 'UseIndex' or 'Iterate'
#SPEED_DETAILS_PER_INDEX_PAGE = SPEED_TOTAL_ITEMS
#SPEED_ITEMS_PER_DETAIL = 100
#SPEED_DETAIL_EXTRA_SIZE = 0

# *** Adjusting individual response times ***
#SPEED_API_T_RESPONSE= 0.5
#SPEED_INDEX_T_RESPONSE = 0
#SPEED_DETAIL_T_RESPONSE = 0

# *** Enable broad search ***
# DEPTH_PRIORITY = 1
# SCHEDULER_DISK_QUEUE = 'scrapy.squeue.PickleFifoDiskQueue'
# SCHEDULER_MEMORY_QUEUE = 'scrapy.squeue.FifoMemoryQueue'
