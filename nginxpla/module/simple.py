from nginxpla.module_config import ModuleConfig
from nginxpla.nginxpla_module import NginxplaModule
from nginxpla.reporter_helper import ReporterHelper


class SimpleModule(NginxplaModule):
    def report(self):
        config = self.config
        return ReporterHelper(config.storage, config.arguments).sql_reports(config.reports)

    def handle_record(self, record) -> str:
        self.is_needed = False
        return record

    def __init__(self, module_config: ModuleConfig):
        self.config = module_config
