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

	$ mkvirtualenv -p /usr/local/bin/python3 impactvizor-pipeline	
    $ cd <source_root>
	$ pip install -r requirements.txt

Create working directories and make them writeable:

    $ mkdir /iv
    $ mkdir /iv/incoming
    $ mkdir /iv/working

(This assumes a working directory in the root directory, which is the default, however this location can be changed with
the `IVETL_WORKING_DIR` environment variable.)

You'll also need to set the permissions of those directories to be writable by your user account, or the account that
you will run the app with.

Then, as at the start of all development sessions, you'll set your shell up using the `local.sh` file:

    $ cd <source_root>
    $ source conf/local.sh

Initialize the Cassandra database schema:

    $ ./init_db.sh
    
(Note that this will drop any existing keyspace with the same name.)

There are various datasets avaialble in the `<source_root>/deploy/data` directory:

* `all_publishers_dml_cql` – All existing live publishers.
* `test_publisher_n_dml.cql` – Various test publishers for general testing and unit tests.

Environment variables
---------------------

The following environment variables are supported:

* `IVETL_ROOT` – The location of the source code.
* `IVETL_CASSANDRA_IP` – The IP address of Cassandra, defaults to `127.0.0.1`
* `IVETL_CASSANDRA_KEYSPACE` - The Cassandra keyspace, defaults to `impactvizor`
* `IVETL_WORKING_DIR` – Main working directory for all pipelines, default to `/iv`
* `IVETL_EMAIL_TO_ADDRESS` – Email address where activity is reported, no default
* `IVETL_EMAIL_FROM_ADDRESS` – The from address for all system emails, default to `impactvizor@highwire.org`

The defaults are a good starting place for local development, however `IVETL_ROOT` and `IVETL_EMAIL_TO_ADDRESS` have no
defaults and must be set.

Running the pipeline
--------------------

The Celery worker can be started as follows:

    $ celery -A ivetl worker --loglevel=info
    
And then you can start Flower at [http://127.0.0.1:5555](http://127.0.0.1:5555) with:

    $ celery flower -A ivetl --address=127.0.0.1 --port=5555
 
If you have test_publisher_1 in the database, you can kick off an example by opening executing the following code:
 
    from ivetl.publishedarticles.UpdatePublishedArticlesPipeline import UpdatePublishedArticlesPipeline
    UpdatePublishedArticlesPipeline.s('test', False).delay()

Tips for required services
--------------------------

### RabbitMQ

This project makes very simple and light usage of RabbitMQ. A default installation should suffice. If you're on Linux or
Mac just use your package manager (`apt-get` or `brew`) to install.

Once installed, start RabbitMQ using:

    $ rabbitmq-server &

And interrogate it using:

    $ rabbitmqctl status
    $ rabbitmqctl list_queues

### Cassandra

For now, we're using the Datastax version of Cassandra. It's available from the
[DataStax website](https://academy.datastax.com/downloads). After installing you can manually start it up using:

    $ <install_directory>/bin/dse cassandra

And the standard Cassandra shell can also be found there:

    $ <install_directory>/bin/cqlsh

Interacting with Cassandra from Python
--------------------------------------

Before you do `cqlengine` type things from the Python command line, you'll need to initialize the connection:

    from ivetl.celery import open_cassandra_connection
    open_cassandra_connection()

And if you're polite, you'll close it down when you're done:

    close_cassandra_connection()

Automated tests
---------------

### Running the test suite

The tests are built on top of the standart `unittest` framework, so running them is as simple as:

    $ python -m unittest
    
You can also run particular test suites or or particular tests, for example:
    
    $ python -m unittest ivetl.pipelines.customarticledata.test_customarticledata

Some notes:

* The tests all use a publisher ID of `test`, so any records associated with that publisher will be lost.
* The smoke tests assume that a Celery worker is running.

### A complete example session

Given the setup mentioned above, with source checked out, env vars set, and services up and running, here are complete
instructions on running tests:

In one terminal, we'll start the Celery worker:

    $ cd $IVETL_ROOT 
    $ workon impactvizor-pipeline
    $ source conf/local.sh 
    $ celery -A ivetl worker --loglevel=info

In another terminal, we'll run the tests:

    $ cd $IVETL_ROOT 
    $ workon impactvizor-pipeline
    $ source conf/local.sh 
    $ python -m unittest

A successful run will take just shy of a minute (at present with 3 pipelines) and should report the following:

    $ python -m unittest
    ...
    ----------------------------------------------------------------------
    Ran 3 tests in 50.540s
    
    OK

Using the UI tools for web app development
------------------------------------------

We require node, bower, grunt, and less to be installed locally. If you have node and npm, you can simply:

    npm install -g bower
    npm install -g grunt-cli
    npm install -g less

Now, install front-end dependencies with bower:

    bower install

To build the first time, or after editing less files or adding/modifying assets:

    grunt build

... or simply leave grunt open and watching for changes with:

    grunt watch

Note that built assets end up in the `/ivweb/app/static/dist` directory but are not added to the git repository.
