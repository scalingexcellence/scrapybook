# -*- coding: utf-8 -*-

# Scrapy settings for generic project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
#

BOT_NAME = 'generic'

SPIDER_MODULES = ['generic.spiders']
NEWSPIDER_MODULE = 'generic.spiders'

# Crawl responsibly by identifying yourself (and your website)
# on the user-agent
#USER_AGENT = 'generic (+http://www.yourdomain.com)'

# Disable S3
AWS_ACCESS_KEY_ID = ""
AWS_SECRET_ACCESS_KEY = ""
