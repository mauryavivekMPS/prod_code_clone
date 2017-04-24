import os
import datetime
import uuid
import decimal
import inspect
from cassandra.cluster import Cluster
from cassandra.query import SimpleStatement
from cassandra.util import OrderedMapSerializedKey
from cassandra.cqlengine.models import Model as CassandraBaseModelClass
from ivetl import models as ivetl_models
from ivetl.common import common


def _format_value(value):
    if value is None:
        return 'NULL'
    else:
        value_type = type(value)
        if value_type in [int, float, bool, uuid.UUID, decimal.Decimal]:
            return str(value)
        elif value_type is datetime.datetime:
            return "'%s'" % value.strftime('%Y-%m-%d %H:%M:%S%z')
        elif value_type is list:
            return "[%s]" % ','.join([_format_value(v) for v in value])
        elif value_type in (dict, OrderedMapSerializedKey):
            return "{%s}" % ','.join(['%s:%s' % (_format_value(k), _format_value(v)) for k, v in value.items()])
    return "'%s'" % value.replace("'", "''").replace("\n", "\\n")


def export_tables(output_dir='.', models=None):
    print('models: %s' % models)
    if models:
        models_to_export = [(m, getattr(ivetl_models, m)) for m in models]
    else:
        models_to_export = [c for c in inspect.getmembers(ivetl_models, inspect.isclass) if issubclass(c[1], CassandraBaseModelClass)]

    print('models to export: %s' % models_to_export)

    cluster = Cluster(common.CASSANDRA_IP_LIST)
    session = cluster.connect()

    for model_name, model_class in models_to_export:
        table_name = model_class.column_family_name()
        cols = list(model_class._columns.keys())
        output_path = os.path.join(output_dir, table_name + '.csv')

        print('Exporting %s to %s' % (model_name, output_path))

        statement = SimpleStatement('select %s from %s limit 10000000;' % (','.join(cols), table_name), fetch_size=1000)

        with open(output_path, 'w') as f:
            f.write(','.join(cols) + '\n')
            for row in session.execute(statement):
                col_values = [_format_value(getattr(row, col)) for col in cols]
                f.write(','.join(col_values) + '\n')
