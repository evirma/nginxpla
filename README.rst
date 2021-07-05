***********************************************************
``nginxpla`` utility for nginx access log real-time metrics
***********************************************************

Inspired by `ngxtop <https://github.com/lebinh/ngxtop>`_

``nginxpla`` is console nginx's log parser and analyser written in python. Fully configurable reports and templates.
Like ``ngxtop`` it allows build ``top``-like custom reports by chosen metrics.
I have tried my best to do it customizable and extendable. 

    ``nginxpla`` is very powefull for troubleshooting and monitoring your Nginx server here and now. 
    It is not suitable for long-term monitoring, because under the hood it has sqlite3. 
    Performance can degrade when large amounts of data accumulate. So, you warned.

``nginxpla`` is config-based utility. It means after first run it create in users home directory folder ``.nginxpla``
with config file in yaml format. When you run ``nginxpla`` it loads configuration, such as log_format for 
file wich you try to analyze and templates with modules. The program is flexible enough 
in configuration to analyze almost any line-by-line logs that can be parsed by regular expressions. 
Modular structure with several modules included.


1. Installation
###############

::
    
    pip install nginxpla
    nginxpla --install
    nano ~/.nginxpla/nginxpla.yaml

2. Usage
########

::

    Usage:
        nginxpla <access-log-file> [options]
        nginxpla <access-log-file> [options] (print) <var> ...
        nginxpla (-h | --help)
        nginxpla --version

    Options:
        -l <file>, --access-log <file>  access log file to parse.
        -f <format>, --log-format <format>  log format as specify in log_format directive. [default: combined]
        -i <seconds>, --interval <seconds>  report interval when running in --top mode [default: 2.0]
        -t <template>, --template <template>  use template from config file [default: main]
        -m <modules>, --modules <modules>  comma separated module list [default: all]

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
        $ nginxpla access_log --sql 'SELECT user_agent, status, count(1) AS count FROM log GROUP BY user_agent, status ORDER BY count DESC LIMIT 100' --fields user_agent,status

Configuration  
-------------

After install configure logs-section:

::

    logs:
        mydomain:
            log_path_regexp: 'mydomain\.access\.log'
            format: "default"
        second_domain_name:
            log_path_regexp: 'second_domain_name\.access\.log'
            format: "custom"
        fallback_to_combined:
            log_path_regexp: '.*'
            format: "combined"

If you use custom nginx log_format or you want configure something different you can define formats in section:

::

    formats:
        default: '$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_x_forwarded_for"'
        combined: '$remote_addr - $remote_user [$time_local] "$request" $status $body_bytes_sent "$http_referer" "$http_user_agent"'
        custom: '$http_x_forwarded_for - [$time_local] "$host" "$request" $status ($bytes_sent) "$http_referer" "$uri $args" "$http_user_agent" [$request_time] [$upstream_response_time]'

Important: After parse $variables will be columns in databse with same name and you can operate them

``regex_formats``-section do the same as ``formats``. If you regex-guru you can speed-up parse by regex. ``regex_formats`` is prefered than simple way, if defined ``format`` and ``regex_format`` with the same name, ``regex_format`` will be used.

SQL suffix
**********

For better visualization I have add suffixes. Just add it to column name in SQL and all row of data will be formatted.
Sql suffix itself will be removed from result table column name.

**_human_size** — size-formatter, convert digits like this 4399151 to this 4,20Mb

Example

::

    $ nginxpla access_log --fields request_path,body_bytes_sent query SELECT request_path, sum(body_bytes_sent) as bytes_sent_human_size GROUP BY request_path ORDER BY bytes_sent_human_size DESC LIMIT 10


Report Table Column Human Name
******************************

All column names from SQL will be transform to string with space-separated words.
But in your sql you should use original column names.

::

    $ nginxpla access_log --fields se,request_path --filter="se=='Google Bot'" query 'SELECT request_path as request_path_by_google_bot, count(1) as count FROM log GROUP BY request_path ORDER BY count DESC LIMIT 10'

    | Request Path By Google Bot   |   Count |
    |------------------------------+---------|
    | /c/202060826/new             |      68 |
    | /c/202060826/discount        |      29 |
    | /c/202001900                 |      28 |
    | /c/202001107                 |      22 |
    | /c/1000008746                |      17 |
    | /c/202060845                 |      17 |
    | /c/202000010                 |      16 |
    | /c/202061131                 |      16 |
    | /c/202062183/new             |      16 |
    | /c/202061132                 |      15 |

    running for 18 seconds, 33923 records processed: 1789.62 req/sec

Print Format
************

For simple queries you can user print syntax:

::

    nginxpla <access-log-file> [options] (print) <var> ...

The print-syntax parser make some useful magick. It is ordering and auto results grouping.
Magick fields is ``count``

::

    $ nginxpla access_log --limit=0 print se count

Example

::

    # Uses Search Engine Module and Pattern Module

    $ nginxpla access_log --filter="se != '-'" --limit=0 print se request_path_pattern count

    | Se           | Request Path Pattern   |   Count |
    |--------------+------------------------+---------|
    | Yahoo Slurp  | Product                |  183522 |
    | Yahoo Slurp  | Rubric                 |  106551 |
    | Yahoo Slurp  | Brand                  |   18200 |
    | Google Bot   | Rubric                 |   17549 |
    | Google Bot   | Product                |   10959 |
    | Google Bot   | Brand                  |    3019 |

    running for 28 seconds, 361730 records processed: 12546.68 req/sec

Modules
-------

ASN Module

Use GeoLite2-ASN.mmdb to get ``asn`` and ``ans_name`` variables to ``record``. ``asn_name`` contains company name from whois

ASN Module Config

.. code-block:: yaml

    asn:
    label: "ASN Top:"
    package: "module.asn"
    class: "AsnModule"
    fields: 
        - asn
        - asn_name
        - remote_addr
        - bytes_sent
        - request_time
    inedxes: 
        - asn_name
    sql: | 
        SELECT
            asn                                         AS ASN,
            asn_name                                    AS Company,
            count(1)                                    AS Count,
            sum(bytes_sent)                             AS sum_bytes_sent_human_size,
            sum(request_time)                           AS total_time,
            avg(request_time)                           AS avg_time,
            count(CASE WHEN status_type = 2 THEN 1 END) AS '2xx',
            count(CASE WHEN status_type = 3 THEN 1 END) AS '3xx',
            count(CASE WHEN status_type = 4 THEN 1 END) AS '4xx',
            count(CASE WHEN status_type = 5 THEN 1 END) AS '5xx'
        FROM log
        GROUP BY asn_name
        HAVING %(--having)s
        ORDER BY %(--order-by)s DESC
        LIMIT  %(--limit)s


Module API
----------

HOW IT WORKS

When a string is parsed into variables, they are concatenated into a record. 
Further, the recording goes in modules (``handle_record``), the module can change or add something to the record. 
After that, only part of the record goes to the database. What exactly gets in depends on the key ``fields`` in the settings file, this is needed for optimization.
Then the ``report`` assembly starts. The report methods are called in the order specified in the config.
The ``handle_report`` method is launched using the same algorithm. But, it receives the resulting report as a parameter.


- ``record`` - dict parsed from log line
- ``report`` - text of all reports 
- ``ModuleConfi`` - object with module settings 

Module it is just a small Class with 3 methods and contructor.

``handle_record`` - method takes only one parameter ``record`` and must return it back. You can modify it.
``report`` - text of report, you can use sql to fetch data from db. If you don't like methods from config.store - you can get connection (``config.store.conn()``) and do what you want
``handle_report`` - takes result report, must return it back

EXAMPLE OF MODULE

.. code-block:: python3
    
    """
    Simple Module

    package: "module.simple"
    class: "SimpleModule"

    """
    from nginxpla.utils import generate_table
    from nginxpla.module_config import ModuleConfig

    class SimpleModule:
        def handle_record(self, record):
            record['some_variable'] = 'some_value'
            return record

        def report(self):
            config = self.config
            [header, data] = config.storage.fetchtable(config.sql, config.arguments)
            return generate_table(header, data)

        def handle_report(self, report: str):
            report += "something to append to the end of entire script's report"
            return report
            
        def __init__(self, module_config: ModuleConfig):
            self.config = module_config