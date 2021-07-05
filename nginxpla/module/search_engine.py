from nginxpla.module_config import ModuleConfig
from nginxpla.utils import generate_table
from nginxpla.nginxpla_module import NginxplaModule


class NginxPlaSearchEngineModule(NginxplaModule):
    def report(self):
        config = self.config

        [header, data] = config.storage.fetchtable(config.sql, config.arguments)
        return generate_table(header, data)

    def handle_record(self, record):
        if self.is_needed is False:
            return record

        required = ['se']
        if self.is_needed is None and not self.config.is_required(set(required)):
            self.is_needed = False
            return record

        ua = record.get('http_user_agent', None)

        options = self.config.options

        se = '-'
        for p in options['engines'].values():
            if self.search(ua, p['searches']):
                se = p['title']
                break

        record['se'] = se
        return record

    @staticmethod
    def search(what, where):
        for s in where:
            if what.find(s) != -1:
                return 1
        return 0

    def __init__(self, module_config: ModuleConfig):
        self.is_needed = None
        self.config = module_config
