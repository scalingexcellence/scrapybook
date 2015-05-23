#!/usr/bin/env python

import time
import string
import telnetlib
import json
from bson import json_util
from datetime import datetime

class Reporter(object):
    
    def __init__(self, schema = None):
        self.schema = schema
        self.first = True
        
    @staticmethod
    def map_value(value):
        try:
            return int(value)
        except:
            try:
                return float(value)
            except:
                try:
                    return bool(value)
                except:
                    return value

    @staticmethod
    def parse_stats(ln):
        if ln.find('Execution engine status') == -1:
            return None
    
        tuples = []
        for i in  map(string.strip, ln.split('\n')):
            parts = map(string.strip, i.split(':'))
            if len(parts) == 2:
                # est() line
                tuples.append((parts[0], Reporter.map_value(parts[1])))
            elif i.startswith('\'{') and i.endswith('}\''):
                stats = json.loads(i[1:len(i)-1], object_hook=json_util.object_hook)
                for kv in stats.iteritems():
                    tuples.append(kv)
    
        return dict(tuples)
    
    def parse(self, ln, secs):
        status = Reporter.parse_stats(ln)
        if status:
            if not self.schema:
                self.schema = map(lambda x: (x,True), sorted(status.keys()))
            
            valid_keys = [v[0] for v in self.schema if v[1]]
            
            if self.first:
                self.first = False
                print ",".join(['gap' if k == '' else k for k in valid_keys])

            print ",".join(['  ' if k == '' else (str(status[k]) if k in status else '-') for k in valid_keys])

tn = telnetlib.Telnet("localhost", 6023)

r = Reporter([
    ('len(engine.slot.scheduler.mqs)', True),
    ('len(engine.downloader.active)', True),
    ('len(engine.scraper.slot.active)', True),
    ('engine.scraper.slot.itemproc_size', True),
    
    ('', True),
    ('len(engine.slot.inprogress)', True),
    ('engine.scraper.slot.active_size', True), # compared with max_active_size=5000000
    
    ('engine.has_capacity()', False),
    ('len(engine.scraper.slot.queue)', False), # Always 0 due to coding stuff
    ('engine.scraper.is_idle()', False),
    ('engine.scraper.slot.needs_backout()', False), # Means that slot.active_size > max_active_size
    ('engine.spider_is_idle(engine.spider)', False), # Means that spider would typically be closing
    ('engine.slot.closing', False),
    ('engine.spider.name', False),
    ('len(engine.slot.scheduler.dqs or [])', False),
    ('time()-engine.start_time', False),

    ('', True),
    ('scheduler/enqueued', False),
    ('scheduler/dequeued', False),
    ('item_scraped_count', True),
    
    ('log_count/INFO', False),
    ('downloader/response_count', False),
    ('response_received_count', False),
    ('scheduler/enqueued/memory', False),
    ('downloader/response_bytes', False),
    ('start_time', False),
    ('scheduler/dequeued/memory', False),
    ('downloader/request_bytes', False),
    ('request_depth_max', False),
    ('log_count/ERROR', False),
    ('downloader/request_method_count/GET', False),
    ('downloader/request_count', False),
])

try:
    lastd = datetime.now()
    
    while True:
        resp = tn.read_very_eager()
        nowd = datetime.now()
        r.parse(resp, (nowd - lastd).total_seconds())
        lastd = nowd
    
        tn.write("est()\nimport json\nfrom bson import json_util\njson.dumps(stats.get_stats(), default=json_util.default)\n")
    
        time.sleep(1)
except EOFError:
    pass
