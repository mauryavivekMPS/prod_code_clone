#!/usr/bin/env python
#
# monitor an sftp.py access log file for new deliveries
#
# Given a filepath to an sftp.py access log watch it for new sessions (user
# logs in in, user changes dir, user delivers files, user logs out), and
# submit any delivered files when the session ends.
#
#

import argparse
import datetime
import logging
import os
import re
import signal
import sys
import threading
import time

from email.utils import unquote
from ivsubmit import api


# map logging level names to numbers
log_level_num = {
	"critical": logging.CRITICAL,
	"error": logging.ERROR,
	"warning": logging.WARNING,
	"info": logging.INFO,
	"debug": logging.DEBUG,
}


# given a log_level_num number return its name
def log_level_name(n):
	next(k for k, v in log_level_num.items() if v == n)


def _parsedt(s):
	"""
	Internal use function to parse a timestamp string in the form
	2019-11-30T01:23:45-0800.  This is the format used by the sftp.py
	logger, which in turn relies on the limited sftrftime syntax where %z
	emits a timezone offset w/o the colon separator required by the ISO
	8601 or RFC 3339 standards.

	It is expected that callers are ensuring s is in the proper format
	before calling _parsedt, if that is not the case an exception will be
	raised.
	"""
	# parse s into list p with items
	# [0] year, [1] month, [2] day, [3] hour, [4] minute, [5] second, [6] tz hhmm
	p = s.replace("-", " ").replace("+", " ").replace("T", " ").replace(":", " ").split(" ")

	# handle hh:mm case (RFC 3339 format, which would be the best format to
	# use, but logging strftime doesn't support it and so sftp.py doesn't
	# use it on python 3.5)
	try:
		if len(p) == 7:
			offset_hh = int(p[6][0:2])
			offset_mm = int(p[6][2:4])
		elif len(p) == 8:
			offset_hh = int(p[6])
			offset_mm = int(p[7])
		else:
			raise("unexpected value passed to _parsedt: " + s)
	except ValueError:
		raise("unexpected value passed to _parsedt: " + s)

	try:
		if s[19] == "-":
			tz = datetime.timezone(
				datetime.timedelta(hours=-offset_hh, minutes=offset_mm))
		elif s[19] == "+":
			tz = datetime.timezone(
				datetime.timedelta(hours=+offset_hh, minutes=offset_mm))
		else:
			raise("unexpected value passed to _parsedt: " + s)
	except IndexError:
		raise("unexpected value passed to _parsedt: " + s)

	try:
		return datetime.datetime(
			int(p[0]), int(p[1]), int(p[2]),
			hour=int(p[3]), minute=int(p[4]), second=int(p[5]),
			tzinfo=tz)
	except ValueError:
		raise("unexpected value passed to _parsedt: " + s)


def _quote(s):
	"""
	Internal use function to return string 's' in a format safe to pass to
	unix sh/bash/zsh shells, single quoting 's' if it contains special
	characters.  If 's' is not a string an empty string is returned.
	"""
	if isinstance(s, str):
		if re.search('[\\s!"#&\'()*,;<=>?[\\]^`{|}~]', s):
			return "'" + s.replace("'", "'\"'\"'") + "'"
		else:
			return s
	return ""


class Filepath:
	"""
	Filepath records the details of an uploaded file
	"""
	def __init__(self, dt, filepath, nbytes):
		self.datetime = dt
		self.filepath = filepath
		self.nbytes = nbytes
		self.log = logging.getLogger(__name__)


class Session:
	"""
	Session records a user session, accumulating submitted files and
	calling the ivsubmit module to submit them to the pipeline.
	"""
	def __init__(self, dt, session_id, user_id, user_name, user_email, notify):
		self.datetime = dt
		self.session_id = session_id
		self.user_id = user_id
		self.user_name = user_name
		self.user_email = user_email
		self.filepath = dict()
		self.notify = notify
		self.log = logging.getLogger(__name__)

	def add_entry(self, dt, filepath, nbytes):
		self.filepath[filepath] = Filepath(dt, filepath, nbytes)

	def rm_entry(self, dt, filepath):
		try:
			del self.filepath[filepath]
		except KeyError:
			# key did not exist
			pass

	def execute(self):
		submitter = api.PipelineSubmitter(self.user_email, notify=self.notify, log=self.log)
		for k, v in self.filepath.items():
			logging.info("adding file for %s: %s", self.user_email, v.filepath)
			if not submitter.add(v.filepath):
				self.log.warning("%s file %s failed to validate", self.user_email, v.filepath)
		if submitter.count() == 0:
			self.log.error("no files passed validation")
		submitter.submit()

	def last_active(self):
		dt = self.datetime
		for k, v in self.filepath.items():
			if v.datetime > dt:
				dt = v.datetime
		return dt

	def manual(self):
		"""manual returns a string detailing how to manually submit the session"""
		return "%s/ivsubmit/ivsubmit.py -email %s %s" % (
			os.getenv("IVETL_ROOT", default="$IVETL_ROOT"),
			_quote(self.user_email),
			' '.join(_quote(v.filepath) for v in self.filepath.values()))


class ActiveSessions:
	"""
	ActiveSessions manages the set of currently active sessions picked up
	from scanning the sftp.py access log.
	"""
	def __init__(self, started=datetime.datetime.now(tz=datetime.timezone.utc), reprocess=False):
		# active sessions
		self.started = started
		self.reprocess = reprocess
		self.active = dict()
		self.log = logging.getLogger(__name__)

		if self.started.tzinfo is None:
			self.log.warn("passed in started value %s missing tzinfo, assuming UTC", self.started)
			self.started.tzinfo = datetime.timezone.utc

	def start(self, dt, session_id, user_id, user_name, user_email, notify):
		if session_id not in self.active:
			session = Session(dt, session_id, user_id, user_name, user_email, notify)
			self.active[session_id] = session
			self.log.debug("started session %s for %s from %s", session_id, user_email, dt)
		else:
			# this should not have happened, it means we either
			# re-parsed an old start session line or we've somehow
			# duplicated a session_id
			pass

	def add_entry(self, dt, session_id, filepath, nbytes):
		if session_id in self.active:
			self.active[session_id].add_entry(dt, filepath, nbytes)
			self.log.debug("session %s added entry %s from %s", session_id, filepath, dt)
		else:
			# We don't have an active session, possibly we're
			# parsing a truncated log or the session was split
			# between two logs, and we never saw the earlier one.
			# Do we send it right away? Send if it's its last
			# modified date is old enough to indicate the session
			# is no no longer active?
			pass

	def rm_entry(self, dt, session_id, filepath):
		if session_id in self.active:
			self.active[session_id].rm_entry(dt, filepath)
			self.log.debug("session %s removed entry %s from %s", session_id, filepath, dt)
		else:
			# We don't have an active session, possibly we're
			# parsing a truncated log or the session was split
			# between two logs, and we never saw the earlier one.
			pass

	def end(self, dt, session_id):
		if session_id in self.active:
			try:
				session = self.active[session_id]

				# if self.reprocess not set and the session
				# ended before this ActiveSessions was started,
				# skip the session
				if not self.reprocess and dt < self.started:
					self.log.warn("skipping session ending at %s, to resubmit manually: %s",
						dt, session.manual())
					return
				try:
					self.log.debug("session %s executing pipeline submission from %s", session_id, dt)
					session.execute()
				except Exception:
					self.log.error("error executing session %s, to resubmit manually: %s", session_id, session.manual(), exc_info=1)
			finally:
				del self.active[session_id]

	def inactive(self, since):
		"""inactive returns a list of any session_id inactive since the specified timedelta"""
		match = []
		now = datetime.datetime.now(tzinfo=datetime.timezone.utc)
		for k, v in self.active.items():
			dt = v.last_active()
			if (now - dt) > since:
				match.append(k)
		return match


class Patterns:
	"""
	Patterns compiles the regular expressions used to parse
	lines out of the sftp.py access log
	"""
	def __init__(self):
		# time matches timestamps in the output by sftp.py, which is
		# close to RFC 3339 with the exception that the timezone does
		# not contain a ':' separator
		# capturing groups:
		#  1 - datetime string (e.g., 2019-11-13T08:32:47-0800)
		# example:
		#  2019-11-12T11:29:41-0800
		self.timestamp = r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}\d{2})'

		# uuid matches a uuid string
		# capturing groups:
		#  1 - uuid
		# example:
		#  ff465c4c-0575-11ea-aa2b-3c6aa7a0de8f]
		self.uuid = r'([a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12})'

		# session_id matches a session id within a logging line output
		# by sftp.py capturing groups:
		#  1 - session_id uuid
		# example:
		#  [ff465c4c-0575-11ea-aa2b-3c6aa7a0de8f]
		self.session_id = '\\[' + self.uuid + '\\]'

		# user_id matches a user id uuid
		# capturing group
		#  1 - user_id uuid
		# example:
		#  55508e06-e168-4192-8e3d-3d2b2b7cc32a
		self.user_id = self.uuid

		# sessionStarted matches an access log entry for the start of a new session
		# capturing groups:
		#  1 - timestamp as produced by sftp.py
		#  2 - session_id
		#  3 - user_id
		#  4 - user_name
		#  5 - user_email
		# example:
		#  2019-11-12T10:23:53-0800 [94efa8a4-0579-11ea-9282-3c6aa7a0de8f] session_started abc310db-644d-4bde-ab10-070a25e9c055 "James A. Robinson" <jimr@highwirepress.com>
		self.sessionStarted = re.compile('^' + self.timestamp + ' ' + self.session_id + ' session_started ' + self.user_id + r' "((?:[^"]|\\")+)" <(.+)>$')

		# sessionStopped matches an access log entry for the end of a session
		# capturing groups:
		#  1 - timestamp as produced by sftp.py
		#  2 - session_id
		# example:
		#  2019-11-12T09:58:34-0800 [ff465c4c-0575-11ea-aa2b-3c6aa7a0de8f] session_ended
		self.sessionStopped = re.compile('^' + self.timestamp + ' ' + self.session_id + ' session_ended$')

		# writeEntry matches an access log entry for the creation of a new file
		# capturing groups:
		#  1 - timestamp as produced by sftp.py
		#  2 - session_id
		#  3 - path
		#  4 - bytes
		# example:
		#  2019-11-12T10:26:02-0800 [deca118a-0579-11ea-92dd-3c6aa7a0de8f] write "/iv/ftp/product/path.txt" (3)
		self.writeEntry = re.compile('^' + self.timestamp + ' ' + self.session_id + r' write "((?:[^"]|\\")+)" \((\d+)\)$')

		# removeEntry matches an access log entry for the deletion of a file
		# capturing groups:
		#  1 - timestamp as produced by sftp.py
		#  2 - session_id
		#  3 - path
		# example:
		#  2019-11-12T10:26:02-0800 [deca118a-0579-11ea-92dd-3c6aa7a0de8f] remove "/iv/ftp/product/path.txt"
		self.removeEntry = re.compile('^' + self.timestamp + ' ' + self.session_id + r' remove "((?:[^"]|\\")+)"$')


class WatchSFTP:
	"""
	WatchSFTP monitors an sftp.py access log
	"""
	def __init__(self, watch, repoll, notify, reprocess):
		self.watch = watch
		self.repoll = repoll
		self.notify = notify
		self.reprocess = reprocess

		self.lock = threading.Lock()
		self.shutdown = threading.Event()

		self.log = logging.getLogger(__name__)
		self.default_log_level = self.log.getEffectiveLevel()

		signal.signal(signal.SIGUSR1, self.cycle_log_level)
		signal.signal(signal.SIGUSR2, self.cycle_log_level)

	def cycle_log_level(self, signum, frame):
		"""
		cycle_log_level handles USR1 and USR2 signals to modify the
		logging levels, USR1 will increase the logging until it reaches
		DEBUG and then flip over to CRITICAL, while USR2 will reset to
		the default logging level DEFAULT_LOG_LEVEL
		"""
		if signum == signal.SIGUSR1:
			level = logger.getEffectiveLevel()
			if level == logging.CRITICAL:
				logfn = logger.error
				level = logging.ERROR
			elif level == logging.ERROR:
				logfn = logger.warning
				level = logging.WARNING
			elif level == logging.WARNING:
				logfn = logger.info
				level = logging.INFO
			elif level == logging.INFO:
				logfn = logger.debug
				level = logging.DEBUG
			else:
				logfn = logger.critical
				level = logging.CRITICAL

			logger.setLevel(level)
			logfn("logger level set to %s", log_level_name(logger.level))
		elif signum == signal.igUSR2:
			logger.setLevel(self.default_log_level)

	def start(self):
		"""
		start will launch the sftp.py access log watcher
		"""

		# set up the sessions tracker, if reprocess is is False only
		# in-flight sessions, or session started after ActiveSessions
		# was stared will be processed.
		sessions = ActiveSessions(reprocess=self.reprocess)

		# file handle for the log file
		fh = None

		# filehandle for newly created log file
		fh_new = None

		# patterns to watch for in the log
		pat = Patterns()

		# previous stat of fh
		prev = None

		# open the log file and process it, then loop forever watching
		# for new log line entries or for new log files
		while True:
			# if shutdown was set, close down the filehandle and
			# terminate
			if self.shutdown.is_set():
				if fh is not None:
					try:
						fh.close()
					except Exception:
						pass
				return

			# if the file does not exist, sleep for repoll seconds
			# then try again
			if not os.path.exists(self.watch):
				time.sleep(self.repoll)
				continue

			# fh_new will be opened if we find the inode has changed
			fh_new = None
			try:
				# compare current inode against the previous inode
				curr = os.stat(self.watch)
				if prev is not None:
					if prev.st_ino != curr.st_ino:
						# different inodes indicate the
						# watched file has been
						# replaced, we'll need to
						# finish reading fh and then
						# swap in fh_new at the end
						fh_new = open(self.watch, "r")
					elif prev.st_size > curr.st_size:
						# the inode has not changed but
						# the file is smaller than it
						# was, we'll assume this means
						# it was truncated, and that
						# we'll need to re-seek to 0
						# and process from there
						fh.seek(0)

				if fh is None:
					fh = open(self.watch, "r")
					nline = 0

				# read to the end of the file, parsing each line for
				# patterns of interest
				for line in fh:
					# if shutdown was set, return
					if self.shutdown.is_set():
						try:
							fh.close()
						except Exception:
							pass
						return

					# look for lines of interest and add
					# them to the active sessions
					line = line.rstrip()
					nline += 1
					self.log.debug("%s:%d %s" % (self.watch, nline, line))
					try:
						m = pat.sessionStarted.match(line)
						if m is not None:
							self.log.debug("%s:%d %s" % (self.watch, nline, "pat.sessionStarted.match"))
							dt = _parsedt(m.group(1))
							session_id = m.group(2)
							user_id = m.group(3)
							user_name = unquote(m.group(4))
							user_email = m.group(5)
							sessions.start(dt, session_id, user_id, user_name, user_email, self.notify)
							continue

						m = pat.writeEntry.match(line)
						if m is not None:
							self.log.debug("%s:%d %s" % (self.watch, nline, "pat.writeEntry.match"))
							dt = _parsedt(m.group(1))
							session_id = m.group(2)
							filepath = unquote(m.group(3))
							nbytes = int(m.group(4))
							sessions.add_entry(dt, session_id, filepath, nbytes)
							continue

						m = pat.removeEntry.match(line)
						if m is not None:
							self.log.debug("%s:%d %s" % (self.watch, nline, "pat.removeEntry.match"))
							dt = _parsedt(m.group(1))
							session_id = m.group(2)
							filepath = unquote(m.group(3))
							sessions.rm_entry(dt, session_id, filepath)
							continue

						m = pat.sessionStopped.match(line)
						if m is not None:
							self.log.debug("%s:%d %s" % (self.watch, nline, "pat.sessionStopped.match"))
							dt = _parsedt(m.group(1))
							session_id = m.group(2)
							sessions.end(dt, session_id)
							continue
					except Exception as e:
						self.log.exception(e)

				# if reprocess is True shut down at this point,
				# since we've reached the end of the file we
				# were processing
				if self.reprocess:
					try:
						fh.close()
					except Exception:
						pass
					return

				# if fh_new was initialized then fh was
				# replaced on the filesystem, so close the
				# handle and replace it with fh_new
				if fh_new is not None:
					try:
						fh.close()
					except Exception:
						pass
					if self.shutdown.is_set():
						return
					fh = fh_new
					nline = 0

				# record prev inode state for the next loop
				prev = curr

				# sleep for self.repoll seconds before
				# repolling
				try:
					self.shutdown.wait(self.repoll)
				except KeyboardInterrupt:
					try:
						fh.close()
					except Exception:
						pass
					return
			except Exception as e:
				self.log.exception(e)

	def stop(self):
		"""
		stop will shut down the watcher
		"""
		self.shutdown.set()


if __name__ == "__main__":
	parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)

	parser.add_argument('-watch', default=None,
		help='path to the access log to watch for new events')

	parser.add_argument('-repoll', default=15, type=int, choices=range(1, 61),
		help='seconds to wait n seconds in-between polling the watched log, in the range 1..60')

	parser.add_argument("-notify", default=False, action='store_true',
		help='send email notification about the success or failure of the submission')

	parser.add_argument("-reprocess", default=False, action='store_true',
		help='reprocess existing entries and then shut down')

	parser.add_argument('-log-level', default='warning',
		help='logging level to use on start-up (critical, error, warning, info, or debug)')

	parser.add_argument('-log-dir', default='/var/log/sftp',
		help='log directory to write log-file under')

	parser.add_argument('-log-file', default='watch-sftp.log',
		help="log file name, or use '-' to write to stdout")

	args = parser.parse_args()

	# set a default watch path if none was provided
	if not args.watch:
		args.watch = "{}/sftp.access.log".format(args.log_dir)

	# setup a basic logger whose output we'll let systemd handle
	if args.log_file == "-":
		handler = logging.StreamHandler()
		handler.setFormatter(logging.Formatter(
			fmt='%(asctime)s %(levelname)s %(name)s %(filename)s:%(lineno)s %(message)s',
			datefmt='%Y-%m-%dT%H:%M:%S%z'))
	else:
		handler = logging.handlers.TimedRotatingFileHandler(
			"{}/{}".format(args.log_dir, args.log_file),
			delay=False, encoding="utf-8", utc=True,
			when="D", interval=1, backupCount=7)

	logger = logging.getLogger()
	logger.addHandler(handler)

	# set the initial logging level
	try:
		logger.setLevel(log_level_num[args.log_level])
	except KeyError:
		sys.stderr.write("invalid -log-level option, valid choices are: critical, error, warning, info, or debug\n")
		sys.exit(1)

	watcher = WatchSFTP(args.watch, args.repoll, args.notify, args.reprocess)
	watcher.start()
