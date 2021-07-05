from nginxpla.module_config import ModuleConfig
from nginxpla.utils import generate_table
from crawlerdetect import CrawlerDetect
from functools import lru_cache
from nginxpla.nginxpla_module import NginxplaModule


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

    @lru_cache(maxsize=102400)
    def parse_crawler(self, ua):
        if self.crawler_detect().isCrawler(ua):
            return self.crawler.getMatches()

        return '-'

    def crawler_detect(self):
        if self.crawler is None:
            self.crawler = CrawlerDetect()

        return self.crawler

    def __init__(self, module_config: ModuleConfig):
        self.crawler_cache = {}
        self.crawler = None
        self.is_needed = None
        self.config = module_config
