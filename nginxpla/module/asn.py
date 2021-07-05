import os
from nginxpla import HOME
from nginxpla.utils import generate_table
from nginxpla.module_config import ModuleConfig
from nginxpla.nginxpla_module import NginxplaModule
import geoip2.database


class AsnModule(NginxplaModule):
    def report(self):
        if self.is_needed is False or not self.file_exists:
            return ''

        config = self.config
        [header, data] = config.storage.fetchtable(config.sql, config.arguments)
        output = generate_table(header, data)

        total_ips = config.storage.fetchone("SELECT count(DISTINCT remote_addr) FROM log", [])
        output += "\nTotal IPs: " + str(total_ips)
        return output

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

    def get_asn(self, ip):
        if ip not in self._cache: 
            with geoip2.database.Reader(self.file) as reader:
                response = reader.asn(ip)
                result = [response.autonomous_system_number, response.autonomous_system_organization]
            self._cache[ip] = result
        return self._cache[ip]

    def __init__(self, module_config: ModuleConfig):
        self.file = HOME + '/geoip/GeoLite2-ASN.mmdb2'
        self.file_exists = os.path.exists(self.file)

        self._cache = {}
        self.config = module_config
