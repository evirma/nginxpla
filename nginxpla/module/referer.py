from nginxpla.module_config import ModuleConfig
from urllib.parse import urlparse
from nginxpla.module.simple import SimpleModule


class RefererModule(SimpleModule):
    def handle_record(self, record):
        if self.is_needed is False:
            return record

        required = ['referer_domain', 'referer']

        if self.is_needed is None and not self.config.is_required(set(required)):
            self.is_needed = False
            return record

        record['referer_domain'] = '-'

        if 'referer' not in record:
            return record

        referer = record['referer']

        if referer == '-':
            return record

        parsed_uri = urlparse(referer)
        record['referer_domain'] = '{uri.netloc}'.format(uri=parsed_uri)

        return record

    def __init__(self, module_config: ModuleConfig):
        super(RefererModule, self).__init__(module_config)

        self.is_needed = None
        self.config = module_config
