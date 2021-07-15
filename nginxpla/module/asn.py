import os
from nginxpla.utils import generate_table
from nginxpla.module_config import ModuleConfig
from nginxpla.nginxpla_module import NginxplaModule
from nginxpla.reporter_helper import ReporterHelper
from functools import lru_cache
import geoip2.database
from geoip2.errors import AddressNotFoundError


class AsnModule(NginxplaModule):
    def report(self):
        if self.is_needed is False or not self.file_exists:
            return ''

        config = self.config
        return ReporterHelper(config.storage, config.arguments).sql_reports(config.reports)

    def handle_record(self, record):
        if self.is_needed is False:
            return record

        required = ['asn', 'asn_name']
        if self.is_needed is None and not self.config.is_required(set(required)):
            self.is_needed = False
            return record

        record['asn'] = '-'
        record['asn_name'] = '-'

        if 'remote_addr' not in record:
            return record

        if self.file_exists:
            [asn, asn_name] = self.get_asn(record['remote_addr'])
            record['asn'] = asn
            record['asn_name'] = asn_name

        return record

    def handle_report(self, report: str):
        return report

    @lru_cache(maxsize=102400)
    def get_asn(self, ip):
        try:
            with geoip2.database.Reader(self.file) as reader:
                response = reader.asn(ip)
                result = [response.autonomous_system_number, response.autonomous_system_organization]
        except AddressNotFoundError:
            result = ['-', '-']

        return result

    def __init__(self, module_config: ModuleConfig):
        options = module_config.options

        self.file = False
        self.file_exists = False

        if options and 'geolite2_asn_file' in options:
            self.file = options['geolite2_asn_file']
            self.file_exists = os.path.exists(self.file)

        self.config = module_config
