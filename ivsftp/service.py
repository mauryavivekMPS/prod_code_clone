#!/usr/bin/env python

import daemon
import logging
import os
import pipes
import signal
import socket
import subprocess
import sys
import threading


class Daemon:
	def __init__(self, args, access_log, log_level=logging.INFO, log_handlers=[]):
		"""Initialize a new Daemon

		A Daemon listens on a specified address and port combination.
		It passes socket connections off to a specified handler class.
		The handler class then manages the actual details of
		negotiating with the client (authentication, authorization,
		service requests).

		Parameters:

		args - Namespace object with the following fields:
			name - name of the service
			addr - address to bind to
			port - port to bind to
			handler - handler class (described below)
			umask - octal umask

		access_log - logging instance for the access log

		log_level - optional default logger level

		log_handlers - optional array of logging.handler instances that
		should be kept open

		Note that args may need additional values based on the
		handler that is specified, the handler should list its
		requirements.

		The handler object should be an instance of threading.Thread
		that accepts the following parameters:
			sock - client socket
			addr - client socket address
			args - the args Namespace object described above
		"""
		self.args = args
		self.args.access_log = access_log

		self.log = logging.getLogger(self.args.name)
		self.log_handlers = log_handlers
		self.log_level = log_level
		self.default_log_level = log_level

		self.mu = threading.Lock()

	def env(self, source, bash="/bin/bash", env=os.environ, log=None):
		""".
		Import bash environment variables from source
		into env (default os.environ)

		Parameters:
		source - bash file to source
		bash - optionally override location of bash
		env - optionally override env to load source into

		Derived from:
			https://github.com/scampersand/envbash-python/
		"""

		if source is None:
			self.log.debug("Daemon.env(None): no-op")
			return

		if not os.path.isfile(source):
			self.log.warn("env called with source=%s, but that file path does not exist", source)
			return

		with open(source):
			pass

		eval_input = '''
			set -a
			source {} >/dev/null
			{} -c "import os; print(repr(dict(os.environ)))"
		'''.format(pipes.quote(source), pipes.quote(sys.executable))

		self.log.info("sourcing %s with %s".format(source, bash))

		with open(os.devnull) as null:
			eval_output, _ = subprocess.Popen(
				[bash, '-c', eval_input],
				stdin=null,
				stdout=subprocess.PIPE,
				stderr=None,
				bufsize=1,
				close_fds=True,
				env=env,
			).communicate()

		if not eval_output:
			raise ValueError("{} evaluation failed".format(source))

		nenv = eval(eval_output)
		if nenv is not None:
			for k, v in nenv.items():
				self.log.debug("setting env[{}] = {}".format(k, v))
				env[k] = v
		else:
			self.log.info("{} produced no environment variables".format(source))

	def cycle_log_level(self, signum, frame):
		with self.mu:
			if self.log_level == logging.CRITICAL:
				self.log_level = logging.ERROR
			elif self.log_level == logging.ERROR:
				self.log_level = logging.WARNING
			elif self.log_level == logging.WARNING:
				self.log_level = logging.INFO
			elif self.log_level == logging.INFO:
				self.log_level = logging.DEBUG
			else:
				self.log_level = logging.CRITICAL
			logging.getLogger().setLevel(self.log_level)

	def reset_log_level(self, signum, frame):
		with self.mu:
			self.log_level = self.default_log_level
			logging.getLogger().setLevel(self.log_level)

	def start(self):
		"""Bind to the args addr:port and serve requests"""
		with self.mu:
			self.run = True

		log_handler_h = []
		for handler in self.log_handlers:
			log_handler_h.append(handler.stream.fileno())

		context = daemon.DaemonContext()

		context.files_preserve = log_handler_h
		context.stdout = sys.stdout
		context.stderr = sys.stderr

		context.detach_process = (not self.args.nofork)
		context.signal_map = {
			signal.SIGUSR1: self.cycle_log_level,
			signal.SIGUSR2: self.reset_log_level,
			signal.SIGINT: self.stop,
			signal.SIGQUIT: self.stop,
			signal.SIGTERM: self.stop,
		}
		context.umask = self.args.umask

		# launch daemon process and start server
		with context:

			# LogStream simulates a Stream object to
			# route stdout/stderr to a logger
			class LogStream(object):
				def __init__(self, name, level):
					self.logger = logging.getLogger(name)
					self.level = level

				def write(self, buf):
					for line in buf.rstrip().splitlines():
						self.logger.log(self.level, line.rstrip())

				def flush(self):
					pass

			sys.stdout.close()
			sys.stdout = LogStream(self.args.name, logging.INFO)

			sys.stderr.close()
			sys.stderr = LogStream(self.args.name, logging.ERROR)

			if hasattr(self.args, 'env'):
				self.env(self.args.env, env=os.environ)

			with self.mu:
				if not self.run:
					return
			try:
				self._serve()
			except Exception:
				logging.exception("self._serve error")
				self.stop(None, None)

	def stop(self, signum, frame):
		"""Stop accepting new requests and shut down"""
		with self.mu:
			self.run = False

		self.log.info("shutting down")
		self.socket.close()
		sys.exit(0)

	def _serve(self):
		"""Listen on args addr:port and launch handler for each new socket"""
		self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.socket .setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.socket.bind((self.args.addr, self.args.port))

		self.log.info("accepting connections on %s:%d/tcp", self.args.addr, self.args.port)

		while True:
			with self.mu:
				if not self.run:
					return

			# listen for new requests and spawn a handler
			try:
				self.socket.listen(1)
				try:
					sock, addr = self.socket.accept()
					with self.mu:
						if not self.run:
							return
					handler = self.args.handler(sock, addr, self.args)
					handler.start()
				except Exception:
					# if we are shutting down do not log an
					# exception for accept
					with self.mu:
						if not self.run:
							return
					self.log.error("accept %s:%d socket error",
						self.args.addr, self.args.port, exc_info=1)
			except Exception:
				self.log.error("listen %s:%d exception:",
						self.args.addr, self.args.port, exc_info=1)
