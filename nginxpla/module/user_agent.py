from nginxpla.module_config import ModuleConfig
from nginxpla.utils import generate_table
from user_agents import parse
from nginxpla.nginxpla_module import NginxplaModule
from functools import lru_cache


class UserAgentModule(NginxplaModule):
    def report(self):
        config = self.config

        if not config.sql:
            return ''

        [header, data] = config.storage.fetchtable(config.sql, config.arguments)
        return generate_table(header, data)

    def handle_record(self, record):
        if self.is_needed is False:
            return record

        required = ['browser',
                    'browser_version',
                    'os',
                    'os_version',
                    'device',
                    'device_brand',
                    'device_version',
                    'is_mobile',
                    'is_tablet',
                    'is_touch_capable',
                    'is_pc',
                    'is_bot',
                    'device_type']

        if self.is_needed is None and not self.config.is_required(set(required)):
            self.is_needed = False
            return record

        user_agent_string = record.get('http_user_agent', '')

        for k in required:
            record[k] = '-'

        if user_agent_string:
            ua = self.parse_ua(user_agent_string)

            record['browser'] = ua.browser.family
            record['browser_version'] = ua.browser.version_string

            record['os'] = ua.os.family
            record['os_version'] = ua.os.version_string

            record['device'] = ua.device.family
            record['device_brand'] = ua.device.brand
            record['device_model'] = ua.device.model

            record['is_mobile'] = 1 if ua.is_mobile else 0
            record['is_tablet'] = 1 if ua.is_tablet else 0
            record['is_touch_capable'] = 1 if ua.is_touch_capable else 0
            record['is_pc'] = 1 if ua.is_pc else 0
            record['is_bot'] = 1 if ua.is_bot else 0

            if record['is_tablet']:
                record['device_type'] = 'tablet'
            elif record['is_mobile']:
                record['device_type'] = 'mobile'
            elif record['is_touch_capable']:
                record['device_type'] = 'touch'
            elif record['is_pc']:
                record['device_type'] = 'pc'
            elif record['is_bot']:
                record['device_type'] = 'bot'

        return record

    @lru_cache(maxsize=102400)
    def parse_ua(self, ua):
        return parse(ua)

    def __init__(self, module_config: ModuleConfig):
        self.ua_cache = {}
        self.is_needed = None
        self.config = module_config
