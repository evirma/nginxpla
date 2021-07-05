"""nginxpla - nginx access log analyzer.

Usage:
    nginxpla <access-log-file> [options]
    nginxpla <access-log-file> [options] (print|top|avg|sum) <var> ...
    nginxpla <access-log-file> [options] (query) <query> ...
    nginxpla (-h | --help)
    nginxpla --install
    nginxpla --version

Options:
    -l <file>, --access-log <file>  access log file to parse.
    -f <format>, --log-format <format>  log format as specify in log_format directive. [default: combined]
    -i <seconds>, --interval <seconds>  report interval when running in --top mode [default: 2.0]
    -t <template>, --template <template>  use template from config file [default: main]
    -m <modules>, --module <modules>  comma separated module list [default: all]

    --info  print configuration info for access_log
    --top  watch for new lines as they are written to the access log.

    -g <var>, --group-by <var>  group by variable [default: ]
    -w <var>, --having <expr>  having clause [default: 1]
    -o <var>, --order-by <var>  order of output for default query [default: count]
    -n <number>, --limit <number>  limit the number of records included in report [default: 10]
    -a <exp> ..., --a <exp> ...  add exp (must be aggregation exp: sum, avg, min, max, etc.) into output

    -v, --verbose  more verbose output
    -d, --debug  print every line and parsed record
    -h, --help  print this help message.
    --version  print version information.

    Advanced:
    -c <file>, --config <file>  nginxpla config file path.
    -e <filter-expression>, --filter <filter-expression>  filter in, records satisfied given expression are processed.
    -p <filter-expression>, --pre-filter <filter-expression>  in-filter expression to check in pre-parsing phase.
    -s <sql-request>, --sql <sql-request>  raw Sql in sqlite format. Table with data is log
    --fields <fields>  Fields to import in sqllite log table, for example, --fields user_agent,status

Examples:
    Print statistics for default template
    $ nginxpla access_log

    Select All indexed data from base
    $ nginxpla access_log --sql select * from log

    Select All indexed data from base
    $ nginxpla access_log --sql 'SELECT user_agent, status, count(1) AS count FROM
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
        print('Config File: %s' % arguments['--config'], end="\n\n")
        print('Log File: %s' % arguments['<access-log-file>'], end="\n\n")
        print('Template: %s' % config.template_name)
        print('Modules: %s' % ','.join(config.modules()))
        print('Fields: %s' % ','.join(config.fields))
    else:
        reporter = Reporter(config, modules)

        if arguments['--top'] and not arguments['print']:
            setup_reporter(reporter, arguments['--interval'])

        Processor(config, modules).process()

        if arguments['print']:
            print_command_builder(arguments, config.storage)
        elif arguments['query']:
            [header, data] = config.storage.fetchtable(' '.join(arguments['<query>']))
            print(generate_simple_table(header, data))
        else:
            print(reporter.report())

        runtime = time.time() - start
        lines = config.storage.count()

        print("\n > running for %i seconds, %i records processed: %.2f req/sec" % (runtime, lines, lines / runtime))


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
