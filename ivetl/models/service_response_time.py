from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class ServiceResponseTime(Model):
    publisher_id = columns.Text(partition_key=True)
    name = columns.Text(primary_key=True)
    from_date = columns.DateTime(primary_key=True)
    until_date = columns.DateTime(primary_key=True)
    sample = columns.Integer()
    units = columns.Text()
    mean = columns.Float()
    standard_deviation = columns.Float()
    variance = columns.Float()
    minimum = columns.BigInt()
    maximum = columns.BigInt()
    percentile_25 = columns.BigInt()
    percentile_50 = columns.BigInt()
    percentile_75 = columns.BigInt()
    percentile_95 = columns.BigInt()
    percentile_99 = columns.BigInt()
