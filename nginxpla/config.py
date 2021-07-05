import os
import re
import yaml
import os.path

from nginxpla.error import error_exit
from nginxpla import HOME, CONFIG_FILE
from nginxpla.storage import LogStorage


class Config(object):
    def __init__(self, config_file: None, arguments):
        self.access_log = arguments['<access-log-file>']
        if self.access_log != 'stdin' and not os.path.exists(self.access_log):
            error_exit('access log file "%s" does not exist' % self.access_log)

        if config_file is None:
            config_file = CONFIG_FILE

        self.config_file = config_file
        if not os.path.exists(config_file):
            error_exit('nginxpla config file not found: %s' % config_file)

        self.arguments = arguments
        self.template_name = arguments['--template']
        self.config = self._load_config(config_file)
        self.fields = self._collect_fields()
        self.indexes = self._collect_indexes()
        self.storage = LogStorage(self.fields, self.indexes)

    def is_field_needed(self, field):
        return field in self.fields

    def fields_union(self, fields: set):
        self.fields = self.fields.union(fields)

    # def set_modules(self, modules: ModuleList):
    #     self.modules = modules

    def modules(self):
        template = self.template(self.template_name)

        result = []
        for module in template['modules']:
            result.append(module)

        return result

    def templates(self):
        return self.config.get('templates', [])

    def template(self, name: str):
        templates = self.templates()
        if name in templates:
            return templates[name]

        return {}

    # def module_list(self) -> ModuleList:
    #     return self.modules

    def aliases(self):
        result = {}

        aliases = self.get('aliases', [])
        for result_value in self.get('aliases', []):
            for alias in aliases[result_value]:
                result[alias] = result_value

        return result

    def get(self, key, default=None):
        return self.config.get(key, default)

    @staticmethod
    def user_default_config():
        return HOME + '/nginxpla.yaml'

    @staticmethod
    def _load_config(config_file):
        cfg = None
        if os.path.isfile(config_file):
            with open(config_file) as f:
                cfg = yaml.safe_load(f)

        return cfg

    def _collect_indexes(self) -> set:
        indexes = self.fields

        template = self.template(self.template_name)
        for module in template['modules']:
            if 'indexes' in template['modules'][module]:
                module_fields = template['modules'][module]['indexes']
                indexes = indexes.union(set(module_fields))

        return indexes.intersection(self.fields)

    def _collect_fields(self) -> set:
        fields = set([])
        if self.arguments['--fields']:
            fields = fields.union(self.arguments['--fields'].split(','))

        if not self.arguments['<var>']:
            template = self.template(self.template_name)
            for module in template['modules']:
                if 'fields' in template['modules'][module]:
                    module_fields = template['modules'][module]['fields']
                    fields = fields.union(set(module_fields))

        fields = fields.union(self._collect_fields_from_var())

        return fields

    def _collect_fields_from_var(self):
        fields = self.arguments['<var>']

        result = []
        disabled_fields = ['count', 'statuses']
        for field in fields:
            if field not in disabled_fields:
                result.append(field)
            elif field == 'statuses':
                result.append('status')
                result.append('status_type')

        return set(result)


def match_log_format(access_log, config: Config) -> str:
    formats = config.get('formats', [])
    if not formats:
        return ''

    format_name = ''

    logs = config.get('logs', [])
    for log_section in logs:
        if re.search(r'seller', access_log):
            format_name = logs[log_section]['format']
            break

    if format_name == '':
        format_name = 'combined'

    if format_name in formats:
        return str(formats[format_name])

    return ''


def match_log_format_regex(access_log, config: Config) -> str:
    regex_formats = config.get('regex_formats')
    if not regex_formats:
        return ''

    logs = config.get('logs', [])

    format_name = ''
    for log_section in logs:
        if re.search(r'seller', access_log):
            format_name = logs[log_section]['format']
            break

    if format_name == '':
        format_name = 'combined'

    if format_name in regex_formats:
        return str(regex_formats[format_name])

    return ''
