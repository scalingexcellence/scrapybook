import treq

from twisted.internet import reactor, task, defer
from twisted.python.failure import Failure

from scrapy.commands import ScrapyCommand
from scrapy.utils.conf import get_config
from scrapy.exceptions import UsageError


class Command(ScrapyCommand):
    requires_project = True

    def run(self, args, opts):
        self._to_monitor = {}
        for name, target in self._get_targets().iteritems():
            if name in args:
                project = self.settings.get('BOT_NAME')
                url = target['url'] + "listjobs.json?project=" + project
                self._to_monitor[name] = url

        if not self._to_monitor:
            raise UsageError("Nothing to monitor")

        l = task.LoopingCall(self._monitor)
        l.start(5)  # call every 5 seconds

        reactor.run()

    @defer.inlineCallbacks
    def _monitor(self):
        all_deferreds = []
        for name, url in self._to_monitor.iteritems():
            d = treq.get(url, timeout=5, persistent=False)
            d.addBoth(lambda resp, name: (name, resp), name)
            all_deferreds.append(d)

        all_resp = yield defer.DeferredList(all_deferreds)

        status = {}
        for (success, (name, resp)) in all_resp:
            if not success:
                print "deferred error"
            elif isinstance(resp, Failure):
                print "got failure: %r" % resp
            elif resp.code == 200:
                json_resp = yield resp.json()
                status[name] = (
                    len(json_resp.get('running', [])),
                    len(json_resp.get('finished', [])),
                    len(json_resp.get('pending', [])),
                )

        to_print = []
        for name in sorted(status.keys()):
            to_print.append("%-20s running: %d, finished: %d, pending: %d" %
                            ((name,) + status[name]))
        print "\033c" + "\n".join(to_print)

    def _get_targets(self):
        cfg = get_config()
        baset = dict(cfg.items('deploy')) if cfg.has_section('deploy') else {}
        targets = {}
        if 'url' in baset:
            targets['default'] = baset
        for x in cfg.sections():
            if x.startswith('deploy:'):
                t = baset.copy()
                t.update(cfg.items(x))
                targets[x[7:]] = t

        return targets
