#!/usr/bin/env python

import os
os.sys.path.append(os.environ['IVETL_ROOT'])

import uuid
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from ivetl.celery import open_cassandra_connection, close_cassandra_connection


class Publisher_Journal(Model):
    publisher_id = columns.Text(primary_key=True)
    product_id = columns.Text(primary_key=True)
    electronic_issn = columns.Text(primary_key=True)
    print_issn = columns.Text()
    journal_code = columns.Text()


class Publisher_Journal_Temporary(Model):
    uid = columns.UUID(primary_key=True, default=uuid.uuid4)
    publisher_id = columns.Text(primary_key=True)
    product_id = columns.Text(primary_key=True)
    electronic_issn = columns.Text(primary_key=True)
    print_issn = columns.Text()
    journal_code = columns.Text()


class Publisher_User(Model):
    user_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    publisher_id = columns.Text(index=True)


class Publisher_User_Temporary(Model):
    uid = columns.UUID(primary_key=True, default=uuid.uuid4)
    user_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    publisher_id = columns.Text(index=True)


if __name__ == "__main__":
    open_cassandra_connection()

    print('Saving journals...')
    for j in Publisher_Journal.objects.all():
        Publisher_Journal_Temporary.objects.create(
            publisher_id=j.publisher_id,
            product_id=j.product_id,
            electronic_issn=j.electronic_issn,
            print_issn=j.print_issn,
            journal_code=j.journal_code,
        )

    print('Saving publisher users...')
    for u in Publisher_User.objects.all():
        Publisher_User_Temporary.objects.create(
            user_id=u.user_id,
            publisher_id=u.publisher_id,
        )

    close_cassandra_connection()
