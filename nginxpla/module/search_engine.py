from nginxpla.module_config import ModuleConfig
from nginxpla.module.simple import SimpleModule
from functools import lru_cache


class SearchEngineModule(SimpleModule):
    def handle_record(self, record):
        if self.is_needed is False:
            return record

        required = ['se']
        if self.is_needed is None and not self.config.is_required(set(required)):
            self.is_needed = False
            return record

        ua = record.get('http_user_agent', None)
        if not ua:
            record['se'] = '-'
        else:
            record['se'] = self.get_search_engine_by_ua(ua)

        return record

    @lru_cache(maxsize=102400)
    def get_search_engine_by_ua(self, ua):
        options = self.config.options
        se = '-'
        for p in options['engines'].values():
            if self.search(ua, p['searches']):
                se = p['title']
                break
        return se

    @staticmethod
    def search(what, where):
        for s in where:
            if what.find(s) != -1:
                return 1
        return 0

    def __init__(self, module_config: ModuleConfig):
        super(SearchEngineModule, self).__init__(module_config)

        self.is_needed = None
        self.config = module_config
