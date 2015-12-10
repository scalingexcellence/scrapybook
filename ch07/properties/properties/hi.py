from scrapy.commands import ScrapyCommand


class Command(ScrapyCommand):
    default_settings = {'LOG_ENABLED': False}

    def run(self, args, opts):
        print("hello")
