from twisted.internet import reactor

from scrapy.commands import ScrapyCommand

from speed.spiders.server import SimpleServer


class Command(ScrapyCommand):
    default_settings = {'LOG_ENABLED': False}

    def short_desc(self):
        return "List available spiders"

    def run(self, args, opts):
        ScrapyCommand.process_options(self, args, opts)

        SimpleServer(self.settings.getint('SPEED_PORT', 9312), self.settings)

        reactor.run()
