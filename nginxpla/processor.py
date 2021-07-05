"""
Log File Lines Processor
"""
import sys
import time
import re
import os

from nginxpla.config import Config
from nginxpla.module_config import ModuleList

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse


def seek_n_lines(f, n):
    assert n >= 0
    pos, lines = n + 1, []
    while len(lines) <= n:
        try:
            f.seek(-pos, 2)
            print("try1")
        except IOError:
            print("try2")
            f.seek(0)
            break
        finally:
            print("try3")
            lines = list(f)
        pos *= 2


def tail(the_file):
    """
    Get the tail of  a given file
    """
    with open(the_file) as f:
        f.seek(0, os.SEEK_END)
        try:
            f.seek(f.tell() - 100000, os.SEEK_SET)
        except IOError:
            f.seek(0, os.SEEK_END)
        except ValueError:
            f.seek(0, os.SEEK_END)

        while True:
            line = f.readline()
            if not line:
                time.sleep(0.1)  # sleep briefly before trying again
                continue
            yield line


def build_source(access_log, arguments):
    # constructing log source
    if access_log == 'stdin':
        lines = sys.stdin
    elif arguments['--top']:
        lines = tail(access_log)
    else:
        lines = open(access_log)
    return lines


def records_transformer(records, handlers, config: Config):
    for record in records:
        aliases = config.aliases()
        for alias in aliases:
            if alias in record and aliases[alias] not in record:
                record[aliases[alias]] = record[alias]

        if 'status' in record:
            record['status'] = int(record['status'])

        if 'bytes_sent' in record:
            record['bytes_sent'] = int(record['bytes_sent'])

        if 'request_time' in record:
            record['request_time'] = float(record['request_time'])

        if 'upstream_response_time' in record:
            urt = record['upstream_response_time']
            record['upstream_response_time'] = 0 if urt == '-' else float(urt)

        if config.is_field_needed('status') or config.is_field_needed('status_type'):
            if 'status' in record:
                record['status_type'] = int(record['status']) // 100
            else:
                record['status_type'] = '-'

        if config.is_field_needed('bytes_sent'):
            if 'bytes_sent' not in record:
                if 'body_bytes_sent' in record:
                    record['bytes_sent'] = int(record['body_bytes_sent'])
                else:
                    record['bytes_sent'] = 0

        if config.is_field_needed('method') or config.is_field_needed('request_path'):
            if 'request_uri' in record:
                record['method'] = '-'
                record['request_path'] = record['request_uri']
            elif 'request' in record:
                request_parts = record['request'].split(' ')
                uri = ' '.join(request_parts[1:-1])

                record['method'] = ''.join(request_parts[0:1])
                record['request_path'] = ''.join(uri.split('?')[0])
            else:
                record['method'] = '-'
                record['request_path'] = '-'

        try:
            for handler in handlers:
                if handler.is_needed is not False:
                    record = handler.handle_record(record)
        except ValueError:
            pass

        yield record


def parse_log(lines, pattern, config: Config, modules: ModuleList):
    handlers = set([])
    for module in modules:
        handlers.add(module.factory())

    matches = (pattern.match(line) for line in lines)
    records = (m.groupdict() for m in matches if m is not None)
    records = records_transformer(records, handlers, config)

    return records


class Processor:
    REGEX_SPECIAL_CHARS = r'([\.\*\+\?\|\(\)\{\}\[\]])'
    REGEX_LOG_FORMAT_VARIABLE = r'\$([a-zA-Z0-9\_]+)'

    def __init__(self, config: Config, modules: ModuleList):
        self.config = config
        self.modules = modules

    def process(self):
        config = self.config
        access_log = config.access_log
        lines = build_source(access_log, config.arguments)

        log_format_regex = config.match_log_format(access_log, 'regex_formats')

        if log_format_regex:
            pattern = re.compile(log_format_regex)
        else:
            log_format = config.match_log_format(access_log, 'format')
            pattern = self.build_pattern(log_format)

        pre_filer_exp = config.arguments['--pre-filter']
        if pre_filer_exp:
            lines = (line for line in lines if eval(pre_filer_exp, {}, dict(line=line)))

        records = parse_log(lines, pattern, config, self.modules)

        filter_exp = config.arguments['--filter']

        if filter_exp:
            records = (r for r in records if eval(filter_exp, {}, r))

        config.storage.import_records(records)

    def build_pattern(self, log_format):
        pattern = re.sub(self.REGEX_SPECIAL_CHARS, r'\\\1', log_format)
        pattern = re.sub(self.REGEX_LOG_FORMAT_VARIABLE, '(?P<\\1>.*)', pattern)

        return re.compile(pattern)
