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

Assumes the availability of the following services:

* Python 3 (with pip and virtualenv)
* Cassandra
* RabbitMQ

Python 

Getting started
---------------

Create working directories and make them writeable:

    mkdir /<something>
    chgrp staff /<something>
    chmod 775 /<something>

Create a Python 3 virtualenv and install python dependencies:

	virtualenv -p /usr/local/bin/python3 <venv_directory>/impactvizor-pipeline
	source <venv_directory>/meerkat/bin/activate
    cd <project_root>
	pip install -r requirements.txt

Add tables to Cassandra:

    ...

Running tests
-------------

Etc etc

    ...