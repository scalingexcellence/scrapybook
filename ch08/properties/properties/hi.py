from scrapy.commands import ScrapyCommand


class Command(ScrapyCommand):
    default_settings = {'LOG_ENABLED': False}

    def short_desc(self):
        return "Says hi"

    def run(self, args, opts):
        print("hi")
