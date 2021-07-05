from __future__ import print_function

import tabulate
from nginxpla.storage import LogStorage
from nginxpla.utils import human_header, human_size


class ReporterHelper:
    def __init__(self, storage: LogStorage, arguments):
        self.storage = storage
        self.arguments = arguments

    def sql_reports(self, reports):
        output = ''
        for report_name in reports:
            sql = reports[report_name].get('sql', '')
            label = reports[report_name].get('label', '')

            if sql:
                output += self.sql_report(label, sql, self.arguments)

        return output

    def sql_report(self, label, sql, arguments):
        [header, data] = self.storage.fetchtable(sql, arguments)

        output = ''

        if label:
            output += label + "\n\n"

        output += self.generate_table(header, data) + "\n\n"
        return output

    @staticmethod
    def generate_table(columns, data):
        column_types = []
        header = []
        for column in columns:
            if column[-11:] == '_human_size':
                column_types.append('human_size')
                column = column[:-11]
            else:
                column_types.append('default')

            header.append(human_header(column))

        tabledata = []
        for row in data:
            index = 0
            new_row = []
            for ctype in column_types:
                if ctype == 'human_size':
                    new_row.append(human_size(row[index]))
                else:
                    new_row.append(row[index])

                index += 1

            tabledata.append(new_row)

        return tabulate.tabulate(tabledata, headers=header, tablefmt='orgtbl', floatfmt='.3f',
                                 colalign=("left", "right", "right", "right", "right"), disable_numparse=[0, 1, 2])
