from nginxpla.module_config import ModuleConfig
from nginxpla.utils import generate_table
from crawlerdetect import CrawlerDetect
from functools import lru_cache
from nginxpla.module.simple import SimpleModule


class CrawlerModule(SimpleModule):
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
        super(CrawlerModule, self).__init__(module_config)

        self.crawler_cache = {}
        self.crawler = None
        self.is_needed = None
        self.config = module_config
