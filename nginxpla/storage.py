import sqlite3
import logging
import sys
from nginxpla.error import error_exit
from contextlib import closing
from tqdm import tqdm


class LogStorage(object):
    def fetchall(self, query, arguments):
        with closing(self.conn.cursor()) as cursor:
            cursor.execute(query % arguments)
            data = cursor.fetchall()
        return data

    def fetchone(self, query, arguments):
        with closing(self.conn.cursor()) as cursor:
            cursor.execute(query % arguments)
            return cursor.fetchone()[0]

    def fetchtable(self, query, arguments=None):
        if arguments is None:
            arguments = []

        with closing(self.conn.cursor()) as cursor:
            cursor.execute(query % arguments)
            columns = (d[0] for d in cursor.description)
            data = cursor.fetchall()

        return [columns, data]

    def init_db(self):
        create_table = 'create table log (%s)' % self.column_list
        with closing(self.conn.cursor()) as cursor:
            logging.info('sqlite init: %s', create_table)
            cursor.execute(create_table)
            for idx, field in enumerate(self.indexes):
                sql = 'create index log_idx%d on log (%s)' % (idx, field)
                logging.info('sqlite init: %s', sql)
                cursor.execute(sql)

    def count(self):
        with closing(self.conn.cursor()) as cursor:
            cursor.execute('select count(1) from log')
            return cursor.fetchone()[0]

    def __init__(self, fields, indexes=None):
        self.started = False
        self.report_queries = None
        self.indexes = indexes if indexes is not None else []
        self.fields = set(fields)

        if len(fields) == 0:
            error_exit("Field list to import in sqlite3 is empty")

        self.column_list = ','.join(fields)
        self.holder_list = ','.join(':%s' % var for var in fields)
        self.conn = sqlite3.connect(':memory:', isolation_level='DEFERRED')
        self.init_db()

    def conn(self):
        self.conn.cursor().execute('''PRAGMA synchronous = OFF''')
        self.conn.cursor().execute('''PRAGMA journal_mode = OFF''')
        return self.conn

    def import_records(self, records):
        sql = 'insert into log (%s) values (%s)' % (self.column_list, self.holder_list)

        bulk = []

        logging.debug('sqlite insert: %s', sql)
        with closing(self.conn.cursor()) as cursor:
            cursor.execute('PRAGMA synchronous = OFF')
            cursor.execute('PRAGMA journal_mode = OFF')
            for r in tqdm(records, unit=' lines', leave=False):
                if not set(self.fields).issubset(r):
                    diff = self.fields.difference(r)
                    sys.stderr.write('Import Records Failed: field "%s" not found in record\n' % ','.join(diff))
                    sys.exit(1)

                self.started = True

                if len(bulk) >= 10000:
                    cursor.executemany(sql, bulk)
                    self.conn.commit()
                    bulk = []

                bulk.append({k: r[k] for k in self.fields})

            cursor.executemany(sql, bulk)
            self.conn.commit()

    def is_started(self):
        return self.started
