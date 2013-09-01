from scrapy.contrib.spiders import Rule
from properties.distextension import links_extracted

import pickle


def distr(base):
    class Master(base):
        name = base.name + "-master"
        __module__ = base.__module__

        if not getattr(base, "index_extractor", None):
            raise Exception("%s doesn't provide an 'index_extractor' attribute"
                            % base.__name__)

        rules = (
            Rule(base.index_extractor,
                 callback='parse_links', follow=True),
        )

        def parse_links(self, response):
            urls = [l.url for l in self.item_extractor.extract_links(response)]
            self.crawler.signals.send_catch_log(
                links_extracted,
                urls=urls,
                spider=self)

    class Worker(base):
        name = base.name + "-worker"
        __module__ = base.__module__

        def __init__(self, *a, **kw):
            super(base, self).__init__(*a, **kw)

            # If it's a worker spider, process only the URLs given
            if self.url.startswith("http"):
                self.start_urls = [self.url]
            else:
                self.start_urls = pickle.loads(self.url)

        if not getattr(base, "parse_item", None):
            raise Exception("%s doesn't provide a 'parse_item' method"
                            % base.__name__)

        # Override default behaviour. This way rules won't be used but items
        # will be parsed directly
        def parse(self, response):
            return self.parse_item(response)

    return Master, Worker
