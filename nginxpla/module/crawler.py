from nginxpla.module_config import ModuleConfig
from nginxpla.utils import generate_table
from crawlerdetect import CrawlerDetect
from nginxpla.nginxpla_module import NginxplaModule
import hashlib


class CrawlerModule(NginxplaModule):
    def report(self):
        config = self.config

        if not config.sql:
            return ''

        [header, data] = config.storage.fetchtable(config.sql, config.arguments)
        return generate_table(header, data)

    def handle_record(self, record):
        if self.is_needed is False:
            return record

        required = ['is_crawler', 'crawler']

        if self.is_needed is None and not self.config.is_required(set(required)):
            self.is_needed = False
            return record

        user_agent_string = record.get('http_user_agent', '')

        for k in required:
            record[k] = '-'

        if user_agent_string:
            record['crawler'] = self.parse_crawler(user_agent_string)

        return record

    def parse_crawler(self, ua):
        result = hashlib.md5(ua.encode())
        md5hash = result.hexdigest()

        if md5hash not in self.crawler_cache:
            if self.crawler_detect().isCrawler(ua):
                self.crawler_cache[md5hash] = self.crawler.getMatches()
            else:
                self.crawler_cache[md5hash] = '-'

        return self.crawler_cache[md5hash]

    def crawler_detect(self):
        if self.crawler is None:
            self.crawler = CrawlerDetect()

        return self.crawler

    def __init__(self, module_config: ModuleConfig):
        self.crawler_cache = {}
        self.crawler = None
        self.is_needed = None
        self.config = module_config
