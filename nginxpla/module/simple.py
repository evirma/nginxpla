from nginxpla.utils import generate_table
from nginxpla.module_config import ModuleConfig
from nginxpla.nginxpla_module import NginxplaModule


class SimpleModule(NginxplaModule):
    def report(self):
        config = self.config
        [header, data] = config.storage.fetchtable(config.sql, config.arguments)
        return generate_table(header, data)

    def handle_record(self, record) -> str:
        self.is_needed = False
        return record

    def __init__(self, module_config: ModuleConfig):
        self.config = module_config
