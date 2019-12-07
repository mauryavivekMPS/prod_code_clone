#!/usr/bin/env python
import argparse
import logging
import logging.handlers
import os
import sys

import api

log_level_num = {
	"critical": logging.CRITICAL,
	"error": logging.ERROR,
	"warning": logging.WARNING,
	"info": logging.INFO,
	"debug": logging.DEBUG,
}

ExitNoEmail = 1
ExitNoFiles = 2
ExitNoValidFiles = 3

if __name__ == "__main__":
	parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

	parser.add_argument("-email", default=None,
		help='email address of user to submit files as')

	parser.add_argument("-notify", default=False, action='store_true',
		help='send email notification aboutthe success or failure of the submission')

	parser.add_argument("-log", default="-",
		help='log filepath or - to write to stderr')

	parser.add_argument("-log-level", default="warning",
		help='logging level to use on start-up (critical, error, warning, info, debug')

	parser.add_argument("files", nargs=argparse.REMAINDER)

	args = parser.parse_args()

	#
	# set up the logger
	#
	log = logging.getLogger()
	if args.log_level in log_level_num:
		log.setLevel(log_level_num[args.log_level])
	else:
		log.setLevel(logging.WARNING)
		log.warning("ignoring invalid -log-level: %s" % args.log_level)

	if args.log == "-":
		root_handler = logging.StreamHandler()
	else:
		root_handler = logging.handlers.TimedRotatingFileHandler(
			args.log, delay=False, encoding="utf-8", utc=True,
			when="D", interval=1, backupCount=7)

	root_handler.setFormatter(logging.Formatter(
		fmt='%(asctime)s %(levelname)s %(name)s %(filename)s:%(lineno)d %(message)s',
		datefmt='%Y-%m-%dT%H:%M:%S%z'))
	log.addHandler(root_handler)

	#
	# check for email
	#
	if args.email is None:
		log.error("ivsubmit requires an -email argument")
		sys.exit(ExitNoEmail)

	#
	# check for files
	#
	if len(args.files) == 0:
		log.error("ivsubmit requires one or more file paths to submit")
		sys.exit(ExitNoFiles)

	#
	# build the PipelineSubmitter
	#
	submitter = api.PipelineSubmitter(args.email, notify=args.notify, log=log)

	for v in args.files:
		v = os.path.abspath(v)
		if not submitter.add(v):
			log.warning("file %s failed to validate" % v)

	if submitter.count() == 0:
		log.error("no files passed validation")
		sys.exit(ExitNoValidFiles)

	submitter.submit()
