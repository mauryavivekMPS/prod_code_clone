impactvizor-pipeline
====================

A data pipeline for the Impact Vizor analytics product.

About
-----

Impact Vizor is a suite of analytics for academic journal publishers. It consists of a series of Tableau workbooks that
sit on top of a Cassandra database which is populated by a series of data pipelines that gather, normalize, join, and
transform data from a number of different first and third-party sources. This project is the implementation of those
pipelines, as well as an internal-facing web-based monitoring tool and an external-facing web-based upload tool.


Installation of 3rd Party Services
----------------------------------

- Install Java 1.8 (http://download.oracle.com/otn-pub/java/jdk/8u181-b13/96a7b8442fe848ef90c96a2fad6ed6d1/jdk-8u181-macosx-x64.dmg)
- Install Cassandra 2.1.14 (https://archive.apache.org/dist/cassandra/2.1.14/) in /opt; follow directions at https://medium.com/@areeves9/cassandras-gossip-on-os-x-single-node-installation-of-apache-cassandra-on-mac-634e6729fad6
- Install RabbitMQ (brew install rabbitmq) (https://www.rabbitmq.com/install-standalone-mac.html)
- Setup schema on cassandra by going to <source code>/deploy/schema; start cqlsh; source 'full_schema_sep_4_2018.cql'

Installation of Vizor
---------------------

Assumes the availability of the following:

* Python 3 (with [virtualenv](https://virtualenv.pypa.io) and [virtualenvwrapper](http://virtualenvwrapper.readthedocs.org))
* Cassandra (running on default ports on localhost)
* RabbitMQ (running on default ports on localhost)

Python dependencies are managed via pip and the `requirements.txt` file.

Assuming you have Python 3, virtualenv, and virtualenvwrapper installed, and the impactvizor-pipeline source cloned,
create a Python 3 virtualenv and install dependencies:

	$ mkvirtualenv -p /usr/local/bin/python3 impactvizor-pipeline	
    $ cd <source_root>
	$ pip install -r requirements.txt

Create working directories and make them writeable:

    $ mkdir /iv
    $ mkdir /iv/incoming
    $ mkdir /iv/working
    $ mkdir /var/log/ivratelimiter
    $ mkdir /var/log/ivweb

(This assumes a working directory in the root directory, which is the default, however this location can be changed with
the `IVETL_WORKING_DIR` environment variable.)

You'll also need to set the permissions of those directories to be writable by your user account, or the account that
you will run the app with.

You need to download the nltk data set to /usr/local/lib/nltk_date
- Transfer data set from dw-work-02.highwire.org/stats/nltk_data.tar.gz

Then, as at the start of all development sessions, you'll set your shell up using the `local.sh` file.
Add this to your .bash_profile:

    $ # Cassandra
    $ export PATH="$PATH:/opt/apache-cassandra-2.1.14/bin"

    $ # IV settings
    $ source /Users/mehtan/Documents/work/highwire/projects/impactvizor-pipeline/conf/local.sh
    $ IVETL_ROOT=/Users/mehtan/Documents/work/highwire/projects/impactvizor-pipeline
    $ export IVETL_ROOT

    $ IVETL_EMAIL_TO_ADDRESS=nmehta+local@highwire.org
    $ export IVETL_EMAIL_TO_ADDRESS

    $ # Update path
    $ export PATH="$PATH:/usr/local/sbin"


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


Creating Admin User
-------------------
If setting up for first time, create an admin user to login with.

    $ Go to <source directory>
    $ workon impactvizor-pipeline
    $ cd <source code root>
    $ ipython
    $ from ivetl.celery import open_cassandra_connection
    $ from ivetl.models import User
    $ open_cassandra_connection()
    $ u = User.objects.create()
    $ u.update(email='[email]', first_name='[first name], last_name='[last name]', user_type=40)
    $ u.set_password('[password]')

Starting Vizor Platform
-----------------------

- Start Cassandra (cassandra -f)
- Start RabbitMQ (rabbitmq-server)
- Start Celery (celery -A ivetl worker --loglevel=info)
- Start UI (./manage.py runserver)
- Start Rate Limiter (gunicorn --workers=1 --worker-class=gthread --threads=120 --bind=0.0.0.0:8082 ivratelimiter.api:app)
- Login to manage portal via http://127.0.0.1:8000/login

And then you can start Flower at [http://127.0.0.1:5555](http://127.0.0.1:5555) with:

    $ celery flower -A ivetl --address=127.0.0.1 --port=5555


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

