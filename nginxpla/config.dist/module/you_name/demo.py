from nginxpla.utils import generate_simple_table
from nginxpla.module_config import ModuleConfig
from nginxpla.nginxpla_module import NginxplaModule


class DemoModule(NginxplaModule):
    """
    Demo Nginxpla Module

    if "?" found in ``request`` fills new variable ``has_query`` (1|0)
    """
    def report(self):
        # It means we have not collect data, no data - no report
        if self.is_needed is False:
            return ''

        sql = "SELECT has_query, count(*) as count FROM log GROUP BY has_query ORDER BY count DESC"

        [header, data] = self.config.storage.fetchtable(sql, self.config.arguments)
        return generate_simple_table(header, data)

    def handle_record(self, record) -> str:
        # If user command params doesn't need in hash_query param
        if self.is_needed is False:
            # !!! always return record !!!
            return record

        # In some runs user we do not have request variable.
        # For example user parse something different from web-server logs
        if 'request' not in record:
            self.is_needed = False
            # !!! always return record !!!
            return record

        # If request contains ? that means it is has_query
        if record['request'].find('?') != -1:
            record['has_query'] = 1
        else:
            record['has_query'] = 0

        # !!! always return record !!!
        return record

    def __init__(self, module_config: ModuleConfig):
        self.config = module_config
