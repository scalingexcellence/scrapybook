BOT_NAME = 'hooksasync'

SPIDER_MODULES = ['hooksasync.spiders']
NEWSPIDER_MODULE = 'hooksasync.spiders'


EXTENSIONS = {'hooksasync.extensions.HooksasyncExtension': 100}
DOWNLOADER_MIDDLEWARES = {
    'hooksasync.extensions.HooksasyncDownloaderMiddleware': 100
}
SPIDER_MIDDLEWARES = {'hooksasync.extensions.HooksasyncSpiderMiddleware': 100}
ITEM_PIPELINES = {'hooksasync.extensions.HooksasyncPipeline': 100}
