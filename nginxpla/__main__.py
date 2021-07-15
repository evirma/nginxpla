"""nginxpla - nginx access log analyzer.

Usage:
    nginxpla <access-log-file> [options]
    nginxpla <access-log-file> [options] (print) <var> ...
    nginxpla <access-log-file> [options] (query) <query> ...
    nginxpla [options]
    nginxpla (-h | --help)
    nginxpla --install
    nginxpla --version

Options:
    -l <file>, --access-log <file>  access log file to parse.
    -f <format>, --log-format <format>  log format as specify in log_format directive. [default: ]
    -i <seconds>, --interval <seconds>  report interval when running in --top mode [default: 2.0]
    -t <template>, --template <template>  use template from config file [default: main]
    -m <modules>, --modules <modules>  comma separated module list [default: all]

    --info  print configuration info for access_log
    --top  watch for new lines as they are written to the access log.

    --fields <fields>  Fields to import in sqlite3 log table, for example, --fields user_agent,status
    -g <var>, --group-by <var>  group by variable [default: ]
    -w <var>, --having <expr>  having clause [default: 1]
    -o <var>, --order-by <var>  order of output for default query [default: count]
    -n <number>, --limit <number>  limit the number of records included in report [default: 10]

    -v, --verbose  more verbose output
    -d, --debug  print every line and parsed record
    -h, --help  print this help message.
    --version  print version information.

    Advanced:
    -c <file>, --config <file>  nginxpla config file path.
    -e <filter-expression>, --filter <filter-expression>  filter in, records satisfied given expression are processed.
    -p <filter-expression>, --pre-filter <filter-expression>  in-filter expression to check in pre-parsing phase.

Examples:
    Show reports for main template
    $ nginxpla access_log

    Show reports for seo template
    $ nginxpla access_log --template seo

    Print reports for main template asn and referrer modules only
    $ nginxpla access_log --template seo --modules asn,referer

    Print report table for request_path counts
    $ nginxpla access_log print request_path count

    Select All indexed data from base
    $ nginxpla access_log query select * from log

    Select User Agent Statuses
    $ nginxpla access_log query 'SELECT user_agent, status, count(1) AS count FROM
      log GROUP BY user_agent, status ORDER BY count DESC LIMIT 100' --fields user_agent,status

    Average body bytes sent of 200 responses of requested path begin with '/catalog':
    $ nginxpla access_log --filter 'status == 200 and request_path.startswith("/catalog")'

    Analyze apache access log from remote machine using 'common' log format
    $ ssh remote tail -f /var/log/apache2/access.log | nginxpla -f custom
"""
from __future__ import print_function, absolute_import
import sys
import time
import logging
from docopt import docopt
from nginxpla.error import message_exit
from nginxpla.config import Config
from nginxpla.reporter import Reporter
from nginxpla.processor import Processor
from nginxpla.utils import command_fields_parser, generate_simple_table, install, setup_reporter, load_template_modules


def process(arguments):
    start = time.time()

    if arguments['--install']:
        install()
        from nginxpla import CONFIG_FILE
        message_exit("Config installed successful. Please, edit %s" % CONFIG_FILE)

    if arguments['<access-log-file>'] is None and not sys.stdin.isatty():
        arguments['<access-log-file>'] = 'stdin'

    #
    # Loading and parse config file
    # It's init modules too
    #
    config = Config(arguments['--config'], arguments)
    modules = load_template_modules(config)

    logging.debug("config file: %s", arguments['--config'])
    logging.debug("config: %s", config)

    #
    # Init Storage and set storage to each ModuleConfig
    #
    if arguments['--info']:
        access_log = arguments['<access-log-file>']
        log_format_regex = config.match_log_format(access_log, 'regex_formats')

        print('Config File: %s' % config.config_file, end="\n\n")
        print('Log File: %s' % arguments['<access-log-file>'], end="\n\n")
        print('Template: %s' % config.template_name)
        print('Modules: %s' % ','.join(config.modules()))
        print('Fields: %s' % ','.join(config.fields))

        if log_format_regex:
            print('Log Format RegExp: %s' % log_format_regex)
        else:
            log_format = config.match_log_format(access_log, 'formats')
            print('Log Format: %s' % log_format)
    else:
        output = ''
        reporter = Reporter(config, modules)

        if arguments['--top'] and not arguments['print']:
            setup_reporter(reporter, arguments['--interval'])

        Processor(config, modules).process()

        if arguments['print']:
            print_command_builder(arguments, config.storage)
        elif arguments['query']:
            [header, data] = config.storage.fetchtable(' '.join(arguments['<query>']))
            output += generate_simple_table(header, data)
        else:
            output += reporter.report()
            print()

        runtime = time.time() - start
        lines = config.storage.count()

        output = output.rstrip("\n")
        output += "\n\n > running for %i seconds, %i records processed: %.2f req/sec" % \
                  (runtime, lines, lines / runtime)

        print(output)


def print_command_builder(arguments, storage):
    fields = arguments['<var>']
    [select, group_by] = command_fields_parser(fields)

    params = {'--select-fields': ",\n\t".join(select),
              '--having': arguments['--having'],
              '--limit': int(arguments['--limit'])}

    if 'count' in fields and arguments['--group-by'] == 'count':
        params['--group-by'] = 'count'
    elif arguments['--group-by'] != '':
        params['--group-by'] = arguments['--group-by']
    else:
        params['--group-by'] = ",\n\t".join(group_by)

    if 'count' in fields and arguments['--order-by'] == 'count':
        params['--order-by'] = 'count'
    else:
        params['--order-by'] = arguments['--order-by']

    query = "SELECT\n\t%(--select-fields)s\nFROM log"

    if params['--group-by']:
        query += "\nGROUP BY %(--group-by)s"

    if params['--having']:
        query += "\nHAVING %(--having)s"

    if params['--order-by']:
        query += "\nORDER BY %(--order-by)s DESC"

    if params['--limit']:
        query += "\nLIMIT %(--limit)s"

    logging.debug("SQL:\n%s", (query % params))

    [header, data] = storage.fetchtable(query, params)
    print(generate_simple_table(header, data))


def main():
    from nginxpla import VERSION
    args = docopt(__doc__, version=VERSION)

    log_level = logging.WARNING
    if args['--verbose']:
        log_level = logging.INFO
    if args['--debug']:
        log_level = logging.DEBUG
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')
    logging.debug('arguments:\n%s', args)

    try:
        process(args)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == '__main__':
    main()
