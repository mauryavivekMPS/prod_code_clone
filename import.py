#!/usr/bin/env python

import django
django.setup()

import sys
import os
from ivetl.celery import open_cassandra_connection, close_cassandra_connection
from cassandra.cqlengine import connection


if __name__ == "__main__":

    open_cassandra_connection()

    if len(sys.argv) == 2:
        input_dir = sys.argv[1]
    else:
        input_dir = '.'

    file_paths = filter(os.path.isfile, [os.path.join(input_dir, f) for f in os.listdir(input_dir) if f.endswith('.csv')])

    for file_path in file_paths:
        table_name = os.path.basename(file_path)[:-4]

        print('Loading data for %s from %s' % (table_name, file_path))

        line_count = 0
        with open(file_path, 'r') as f:
            cols = f.readline().strip()

            for line in f.readlines():
                s = 'insert into %s (%s) values (%s);' % (table_name, cols, line.strip().replace("\\n", "\n"))
                connection.execute(s)
                line_count += 1

        print('Loaded %s values' % line_count)

    close_cassandra_connection()
