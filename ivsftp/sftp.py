#!/usr/bin/env python

import argparse
import logging
import logging.handlers
import service
import sys

from iv_auth_db import IVAuthDBServer
from iv_sftp_fs import IVSFTPFileSystemServer
from sftp_transport import SFTP_Transport

log_level_num = {
	"critical": logging.CRITICAL,
	"error": logging.ERROR,
	"warning": logging.WARNING,
	"info": logging.INFO,
	"debug": logging.DEBUG,
}

if __name__ == "__main__":
	parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

	# Daemon args
	parser.add_argument('-addr', default='0.0.0.0',
		help='ip address to bind to')
	parser.add_argument('-port', type=int, default=22,
		help='port number to bind to')
	parser.add_argument('-env', default=None,
		help='source environment variables from this file')
	parser.add_argument('-sftpdir', default='/iv/ftp',
		help='base directory for all sftp accounts')
	parser.add_argument('-log-dir', default='/var/log/sftp',
		help='base directory for sftp logs')
	parser.add_argument('-log-file', default='sftp.log',
		help='log file name under log-dir')
	parser.add_argument('-log-level', default='warning',
		help='logging level to use on start-up (critical, error, warning, info, debug')
	parser.add_argument('-umask', type=int, default=0o002,
		help='file creation umask')
	parser.add_argument('-nofork', default=False, action='store_true',
		help='do not fork the daemon')
	parser.add_argument('-name', default='sftp',
		help='name of the service')

	# Server args
	parser.add_argument('-dsa-key', default='/etc/ssh/ssh_host_dsa_key', help='ssh dsa key')
	parser.add_argument('-ecdsa-key', default='/etc/ssh/ssh_host_ecdsa_key', help='ssh ecdsa key')
	parser.add_argument('-ed25519-key', default='/etc/ssh/ssh_host_ed25519_key', help='ssh ed25519 key')
	parser.add_argument('-rsa-key', default='/etc/ssh/ssh_host_rsa_key', help='ssh rsa key')

	# SFTPServer args

	# initialize args
	args = parser.parse_args()
	args.handler = SFTP_Transport

	args.si = IVAuthDBServer
	args.si_args = [args]

	args.sftp_si = IVSFTPFileSystemServer
	args.sftp_si_args = [args]

	# construct the root logger for handling debug,
	# info, etc., level logging
	try:
		log_level = log_level_num[args.log_level]
	except KeyError:
		sys.stderr.write("invalid -log-level option, valid choices are: critical, error, warning, info, or debug\n")
		sys.exit(1)
	root_log = logging.getLogger()
	root_log.setLevel(log_level)

	root_handler = logging.handlers.TimedRotatingFileHandler(
		"{}/{}".format(args.log_dir, args.log_file),
		delay=False, encoding="utf-8", utc=True,
		when="D", interval=1, backupCount=7)

	root_handler.setFormatter(logging.Formatter(
		fmt='%(asctime)s %(levelname)s %(name)s %(filename)s:%(lineno)d %(message)s',
		datefmt='%Y-%m-%dT%H:%M:%S%z'))
	root_log.addHandler(root_handler)

	# construct the 'access' logger for recording
	# sftp client put/get activitiy
	access_log = logging.getLogger("{}.access".format(args.name))
	access_log.propagate = False
	access_log.setLevel(logging.INFO)

	access_handler = logging.handlers.TimedRotatingFileHandler(
		"{}/{}.access.log".format(args.log_dir, args.name),
		delay=False, encoding="utf-8", utc=True,
		when="D", interval=1, backupCount=7)

	access_handler.setFormatter(logging.Formatter(
		fmt='%(asctime)s %(message)s', datefmt='%Y-%m-%dT%H:%M:%S%z'))
	access_log.addHandler(access_handler)

	# launch the service
	server = service.Daemon(args, access_log=access_log, log_level=log_level, log_handlers=[access_handler, root_handler])
	server.start()
