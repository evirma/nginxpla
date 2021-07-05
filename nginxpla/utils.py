# -*- coding: utf-8 -*-
from __future__ import division, absolute_import

import os
import atexit
import signal
import curses
import tabulate
from shutil import copytree
from nginxpla import HOME
from nginxpla.error import error_exit
from nginxpla.reporter import Reporter
from nginxpla.config import Config
from nginxpla.module_config import ModuleList, ModuleConfig

DATA_DIR = os.path.join(HOME, 'data')


def makedirs(name, mode=0o750):
    try:
        os.makedirs(name, mode)
    except OSError:
        pass


def setup_reporter(reporter: Reporter, interval):
    scr = curses.initscr()
    atexit.register(curses.endwin)

    def print_report(sig, frame):
        output = reporter.report()

        scr.erase()
        try:
            scr.addstr(output)
        except curses.error:
            pass
        scr.refresh()

    signal.signal(signal.SIGALRM, print_report)
    interval = float(interval)
    signal.setitimer(signal.ITIMER_REAL, 0.1, interval)


def install():
    cwd = os.path.dirname(os.path.abspath(__file__))
    dist_dir = cwd + '/config'

    if os.path.exists(HOME):
        error_exit("Config directory " + HOME + " already exists. If you want reinstall, remove directory " + HOME)

    copytree(dist_dir, HOME)


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


def generate_simple_table(columns, data):
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

    return tabulate.tabulate(tabledata, headers=header, tablefmt='orgtbl', floatfmt='.3f')


def human_size(num, suffix='b'):
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


def human_header(header):
    words = header.split('_')
    words = [word.capitalize() for word in words]

    return ' '.join(words)


def command_fields_parser(fields):
    select = []
    group = []
    for field in fields:
        if field == 'statuses':
            select.append("count(CASE WHEN status_type = 2 THEN 1 END) AS '2xx'")
            select.append("count(CASE WHEN status_type = 3 THEN 1 END) AS '3xx'")
            select.append("count(CASE WHEN status_type = 4 THEN 1 END) AS '4xx'")
            select.append("count(CASE WHEN status_type = 5 THEN 1 END) AS '5xx'")
        elif field == 'sum_request_time':
            select.append('sum(request_time) as sum_request_time')
        elif field == 'avg_request_time':
            select.append('sum(request_time) as sum_request_time')
        elif field == 'request_time':
            select.append('sum(request_time) as sum_request_time')
            select.append('avg(request_time) as avg_request_time')
        elif field == 'sum_bytes_sent':
            select.append('sum(bytes_sent) as sum_b_sent_human_size')
        elif field == 'avg_bytes_sent':
            select.append('sum(bytes_sent) as sum_b_sent_human_size')
        elif field == 'bytes_sent':
            select.append('sum(bytes_sent) as sum_b_sent_human_size')
            select.append('round(avg(bytes_sent)) as avg_b_sent_human_size')
        elif field == 'count':
            select.append('count(*) as count')
        elif field == 'statuses':
            select.append('count(*) as count')
        else:
            select.append(field)
            group.append(field)

    return [select, group]


def load_template_modules(config: Config):
    template = config.template_name
    templates = config.templates()
    modules = []
    for module_name in config.modules():
        module = ModuleConfig(module_name, templates[template]['modules'][module_name], config)
        modules.append(module)

    module_list = ModuleList(modules)
    module_list.set_storage(config.storage)

    return module_list
