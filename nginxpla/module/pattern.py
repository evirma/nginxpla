import re
from nginxpla.error import error_exit
from nginxpla.module_config import ModuleConfig
from nginxpla.utils import generate_table
from nginxpla.nginxpla_module import NginxplaModule


class PatternModule(NginxplaModule):
    def report(self):
        config = self.config
        [header, data] = config.storage.fetchtable(config.sql, config.arguments)
        return generate_table(header, data)

    def handle_record(self, record):
        if self.is_needed is False:
            return record

        if self.is_needed is None and not self.config.is_required('request_path_pattern'):
            self.is_needed = False
            return record

        request_path_pattern = record.get('request_path', None)

        options = self.config.options

        if not options:
            error_exit("Options not found")

        sections = int(options['sections'])
        if sections > 0:
            parts = request_path_pattern.split('/', sections + 1)[1:sections + 1]
            request_path_pattern = '/' + '/'.join(parts) + '...'

        for p in options['replaces'].values():
            request_path_pattern = re.sub(p['from'], p['to'], request_path_pattern)

        record['request_path_pattern'] = request_path_pattern
        return record

    def __init__(self, module_config: ModuleConfig):
        self.is_needed = None
        self.config = module_config
