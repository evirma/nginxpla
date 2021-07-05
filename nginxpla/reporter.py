from __future__ import print_function

from nginxpla.config import Config
from nginxpla.module_config import ModuleList


class Reporter:
    def __init__(self, config: Config, modules: ModuleList):
        self.config = config
        self.modules = modules

    def report(self):
        if not self.config.storage.is_started():
            return ''

        output = []

        for module in self.modules:
            label = module.label
            if label:
                label += "\n"

            module_report = module.factory().report()
            output.append('%s%s' % (label, module_report))

        report = ''.join(output)

        for module in self.modules:
            report = module.factory().handle_report(report)

        return report
