impactvizor-pipeline
====================

A data pipeline for the Impact Vizor analytics product.

About
-----

Impact Vizor is a suite of analytics for academic journal publishers. It consists of a series of Tableau workbooks that
sit on top of a Cassandra database which is populated by a series of data pipelines that gather, normalize, join, and
transform data from a number of different first and third-party sources. This project is the implementation of those
pipelines, as well as an internal-facing web-based monitoring tool and an external-facing web-based upload tool.

Prerequisites
-------------

Assumes the availability of the following:

* Python 3 (with [virtualenv](https://virtualenv.pypa.io) and [virtualenvwrapper](http://virtualenvwrapper.readthedocs.org))
* Cassandra (running on default ports on localhost)
* RabbitMQ (running on default ports on localhost)

Python dependencies are managed via pip and the `requirements.txt` file.

Getting started
---------------

Assuming you have Python 3, virtualenv, and virtualenvwrapper installed, and the impactvizor-pipeline source cloned,
create a Python 3 virtualenv and install dependencies:

	mkvirtualenv -p /usr/local/bin/python3 impactvizor-pipeline	
    cd <source_root>
	pip install -r requirements.txt

Create working directories and make them writeable:

    mkdir /iv
    mkdir /iv/incoming
    mkdir /iv/working

(This assumes a working directory in the root directory, which is the default, however this location can be changed with
the `IVETL_WORKING_DIR` environment variable.)

You'll also need to set the permissions of those directories to be writable by your user account, or the account that
you will run the app with.

Add tables to Cassandra:

    ...

Environment variables
---------------------

The following environment variables are supported:

* `IVETL_CASSANDRA_IP` – The IP address of Cassandra, defaults to `127.0.0.1`
* `IVETL_CASSANDRA_KEYSPACE` - The Cassandra keyspace, defaults to `impactvizor`
* `IVETL_WORKING_DIR` – Main working directory for all pipelines, default to `/iv`
* `IVETL_EMAIL_TO_ADDRESS` – Email address where activity is reported, no default
* `IVETL_EMAIL_FROM_ADDRESS` – The from address for all system emails, default to `impactvizor@highwire.org`

The defaults are a good starting place for local development, however `IVETL_EMAIL_TO_ADDRESS` has no default and must
be set.

Running tests
-------------

Etc etc

    ...

Administering with Fabric
-------------------------

We have a fabfile that can do a bunch of deployment, testing, and interrogation tasks.

    $ fab -l
    Available commands:

        git_pull
        git_status
        ivetl_conf
        restart_celery
        restart_ivetl
        restart_rabbitmq
        start_celery
        start_rabbitmq
        stop_celery
        stop_rabbitmq
        update_ivetl
        update_pip

The most common one will be to roll out a new version of meerkat:

    fab -H impactvizor_prod01 update_ivetl

(This assumes that you have `impactvizor_prod01` set up in your `.ssh/config` file, obviously.)

This will call several other tasks to pull the latest from git, update the local environment, and then
restart RabbitMQ and Celery.