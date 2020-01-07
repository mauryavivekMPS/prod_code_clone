#!/usr/bin/env python

import logging
import os
import paramiko
import threading
import time


class SFTP_Transport(threading.Thread):
	""" SFTP_Transport uses paramiko to construct an sftp service

	It requires that implementations of paramiko.ServerInterface (which
	handles authentication details) and paramiko.SFTPServerInterface (which
	handles SFTP request details) be implemented and passed in via a
	Namespace object 'args'.  See the documentation of __init__ for
	details.
	"""

	def __init__(self, sock, addr, args):
		"""Initialize a new Server_Framework object

		SFTP_Transport initialization parameters:
			sock - client socket
			addr - client socket address
			args - Namespace object from argparse.parse_args (described below)

		The args Namespace object is expected to contain at least the
		following fields:

			log = Logger
			si = class implementing paramiko.ServerInterface
			sftp_si = class implementing the paramiko.SFTPServerInterface

			dsa_key - path to SSH DSA Host key, or 'None'
			ecdsa_key - path to SSH ECDSA Host Key, or 'None'
			ed25519_key - path to SSH ED25519 Host Key, or 'None'
			rsa_key - path to SSH RSA Host Key, or 'None'
		"""
		threading.Thread.__init__(self)

		self.args = args

		self.sock = sock
		self.addr = addr
		self.log = logging.getLogger(self.args.name)

	def run(self):
		"""Process the request on the socket"""
		self.log.info("running %s handler for %s", self, self.addr)

		# server interface (user authentication layer)
		si = None
		try:
			si = self.args.si
		except Exception as e:
			self.log.exception(e)
		if si is None:
			self.log.error("args.si paramiko.ServerInterface was not set by caller")
			return
		if not issubclass(si, paramiko.ServerInterface):
			self.log.error("args.si not a subclass of paramiko.ServerInterface: %s", si)
			return

		# server interface args, if any
		si_args = []
		try:
			si_args = self.args.si_args
		except Exception:
			pass

		# sftp server interface (sftp implementation)
		sftp_si = None
		try:
			sftp_si = self.args.sftp_si
		except Exception:
			pass

		if sftp_si is None:
			self.log.error("args.sftp_si paramiko.SFTPServerInterface was not set by caller")
			return

		if not issubclass(sftp_si, paramiko.SFTPServerInterface):
			self.log.error("args.sftp_si not a subclass of paramiko.SFTPServerInterface: %s", sftp_si)
			return

		# sftp server interface args, if any
		sftp_si_args = []
		try:
			sftp_si_args = self.args.sftp_si_args
		except Exception:
			pass

		# ssh server authentication (ssh host keys)
		host_keys = {}
		for k in ['dsa_key', 'ecdsa_key', 'ed25519_key', 'rsa_key']:
			v = vars(self.args)[k]
			if v is not None and v != 'None' and os.path.isfile(v):
				try:
					if k == 'dsa_key':
						host_keys.update({v: paramiko.DSSKey(filename=v)})
					elif k == 'ecdsa_key':
						host_keys.update({v: paramiko.ECDSAKey(filename=v)})
					elif k == 'ed25519_key':
						host_keys.update({v: paramiko.Ed25519Key(filename=v)})
					elif k == 'rsa_key':
						host_keys.update({v: paramiko.RSAKey(filename=v)})
					else:
						self.log.warning("skipping unhandled SSH host Key id: %s", k)
				except Exception as e:
					self.log.info("unable to parse SSH Host Key as %s: %s: %s", k, v, e)

		if len(host_keys) == 0:
			self.log.error("args must contain at least one of rsa_key, dsa_key, ecdsa_key, or ed25519_key, and must be valid file readable by the process")
			return

		# we should be able to setup the sftp system at this point,
		# pass the socket into the paramiko Transport layer
		try:
			transport = paramiko.Transport(self.sock)
		except Exception as e:
			self.log.error("error initializing paramiko.Transport on %s", self.sock)
			self.log.exception(e)
			return

		# register our ssh host keys
		for k, v in host_keys.items():
			try:
				transport.add_server_key(v)
				self.log.debug("registered SSH Host Key %s", k)
			except Exception as e:
				self.log.error("error registering SSH Host Key %s", k)
				self.log.exception(e)

		# set the subsystem handler, which implements the actual sftp
		# server functionality
		try:
			transport.set_subsystem_handler(
				'sftp', paramiko.SFTPServer, sftp_si, *sftp_si_args)
		except Exception as e:
			self.log.error("error initializing subsystem handler using %s", sftp_si)
			self.log.exception(e)
			return

		# initialize the server, which handles the client
		# authentication dance
		server = None
		try:
			server = si(*si_args)
		except Exception as e:
			self.log.error("error initializing server using %s", si)
			self.log.exception(e)
			return

		# launch the server, which will handle ssh authentication
		# via 'si' and sftp via 'sftp_si'.
		try:
			event = threading.Event()
			transport.start_server(event=event, server=server)

			# wait for negotiation to complete
			event.wait()

			# spin off the connection and wait for it to be closed
			channel = transport.accept()
			while transport.is_active():
				time.sleep(1)
			try:
				if channel is not None:
					channel.close()
			except Exception:
				pass

		except Exception as e:
			self.log.error("exception caught running server %s", server)
			self.log.exception(e)
			return
