NAME

  sftp.py - sftp server

SYNOPSIS

  python sftp.py [ option ... ]

  python watch-sftp.py [ option ... ]

DESCRIPTION

  The sftp.py command implements an sftp service and logs session activity to a
  log directory, by default /var/log/sftp/.  A companion program, watch-sftp.pt
  watches the session log and triggers submission of delivered files to the
  IVETL pipeline.

  Users are allowed to log in using the email address and passwords stored in
  the impactvizor Cassandra keyspace.

  sftp.py options:
  
    -addr
      ip address to bind to, by default 0.0.0.0
  
    -port
      port number to bind to, by default 22
  
    -env
      by default the existing environment is used to check for variables of
      interest, but a seprate sh file may be specified here to override those
      values (see ENVIRONMENT below)
  
    -sftpdir
      base directory for sftp accounts, by default /iv/ftp (sharing the same
      space as the ftp service)

    -log-dir
      log directory to store debugging and session logs under, by default
      /var/log/sftp
  
    -log-file
      log file name for debugging, by default sftp.log

    -log-level
      logging level for -log-file (debug, info, warning, error, critical), by
      default warning

    -umask
      umask for files created via sftp, by default 002

    -nofork
      flag to prevent forking of the daemon process

    -name
      name of the service used in logging, by default sftp

  watch-sftp.py options:

    -watch
      path to the sftp access log to watch for new events, by default
      /var/log/sftp/sftp.access.log

    -repoll
      number of seconds to wait between polling the log file, valid values are
      between 1 and 61, with the default being 15

    -notify
      send email notifications to users when a file is processed

    -reprocess
      flag to reprocess every session seen in the sftp.access.log and then quit

    -log-dir
      log directory to store debugging and session logs under, by default
      /var/log/sftp

    -log-file
      log file name for debugging, by default watch-sftp.log

    -log-level
      logging level for -log-file (debug, info, warning, error, critical), by
      default warning

FILES

  /iv/conf/sftp_prod.sh
    set environment variables used throughout the impactvizor codebase

  /etc/init.d/sftp
    script to start, stop, or restart the sftp service

  /etc/init.d/watch-sftp
    script to start, stop, or restart the watch-sftp service

ENVIRONMENT

  IVETL_PROD
    Set to 1 when running inside a production environment, otherwise unset

  IVETL_LOCAL
    Set to 1 when running inside a developer's local environment, otherwise unset

  IVETL_QA
    Set to 1 when running inside a development environment, otherwise unset

  IVETL_ROOT
    Path to the impactvizor-pipeline codebase, e.g., /iv/impactvizor-pipeline

  IVETL_CASSANDRA_IP
    Comma separated list of Cassandra nodes to connect to

  DJANGO_SETTINGS_MODULE
    Name of the module used by Django for its settings, this should be within
    the python import path (see PYTHONPATH below)

  IVETL_RABBITMQ_BROKER_URL
    Semi-colon separated list of connection URLs for the RabbitMQ client

  IVSFTP_ADDR
    IP Address of the sftp server

  IVSFTP_PORT
    Port address of the sftp server

  PYTHONPATH
    Python module path, which should include IVETL_ROOT

SOURCE

  git@github.com:highwire/impactvizor-pipeline/
