from abc import ABCMeta, abstractmethod


class NginxplaModule:
    __metaclass__ = ABCMeta

    is_needed = None

    @abstractmethod
    def report(self) -> str:
        pass

    def handle_report(self, report: str) -> str:
        return report
