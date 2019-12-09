#!/usr/bin/env python

import atexit
import logging
import os
import paramiko
import threading

from cassandra.connection import ConnectionException
from ivetl.common import common
from ivetl.celery import open_cassandra_connection, close_cassandra_connection
from ivetl.models import PublisherMetadata, User

iv_auth_db_server_pool_mutex = threading.Lock()
iv_auth_db_server_pool_init = False


class IVAuthDBServer(paramiko.ServerInterface):
	def __init__(self, args):
		"""IVAuthDBServer implements paramiko.ServerInterface using the
		impact vizor cassandra database to manage authentication
		requests.

i		Parameters:

		args - Namespace object with the following fields:
			log - Logger instance

		Other requirements:
			os.environ['IVETL_CASSANDRA_IP'] - set to the comma-separated list of addr:port for the cassandra nodes

		"""
		self.args = args
		self.log = logging.getLogger(self.args.name)

		self.home_dir = None
		self.publishers = []
		self.user = None

		self.setup_cassandra()

	def setup_cassandra(self, reinitialize=False):
		""" setup_cassandra initializes the cassandra connection

		If the parameter reinitialize=True is passed then any
		existing cassandra connections will be closed before
		being re-opened.
		"""
		global iv_auth_db_server_pool_mutex
		global iv_auth_db_server_pool_init
		with iv_auth_db_server_pool_mutex:
			if iv_auth_db_server_pool_init is False or reinitialize is True:
				if reinitialize is True:
					try:
						self.log.error("setup_cassandra(reinitialize=True) called, attempting to close cassandra connections before reinitializing")
						close_cassandra_connection()
						iv_auth_db_server_pool_init = False
					except Exception as e:
						self.log.error("error closing cassandra connections")
						self.log.exception(e)
				try:
					open_cassandra_connection()
					iv_auth_db_server_pool_init = True
					atexit.register(close_cassandra_connection)
				except Exception as e:
					self.log.error("error initializing cassandra connection")
					self.log.exception(e)

	def get_allowed_auths(self, username):
		""" get_allowed_auths returns the authentication methods allowed for this connection """
		return "password"

	def check_auth_password(self, username, password):
		""" check_auth_password checks that a given username/password combination is valid """
		self.log.info("check_auth_password request: username = %s, password = ******", username)
		try:
			user = User.objects.get(email=username)

			if user.check_password(password):
				self.user = user

				if self.user.is_superuser:
					self.publishers = PublisherMetadata.objects.all()
				else:
					self.publishers = self.user.get_accessible_publisher()

				user_dir_name = self.user.email.replace('@', '_').replace('.', '_')
				self.home_dir = os.path.join(common.BASE_FTP_DIR, user_dir_name)

				for publisher in self.publishers:
					for product_id in publisher.supported_products:
						product = common.PRODUCT_BY_ID[product_id]
						if product['cohort']:
							continue
						for pipeline in [p['pipeline'] for p in product['pipelines']]:
							if not pipeline.get('has_file_input'):
								continue
							pipeline_dir = common.get_ftp_dir_name(product_id, pipeline['id'])
							full_dir = os.path.join(self.home_dir, publisher.publisher_id, pipeline_dir)
							os.makedirs(full_dir, exist_ok=True)

				return paramiko.AUTH_SUCCESSFUL
			else:
				self.log.info("abject failure...")
		except User.DoesNotExist:
			self.log.info("IVAuthDBServer.check_auth_password request: username not found: %s", username)
		except ConnectionException as e:
			self.log.error("IVAuthDBServer.check_auth_password request: cassandra connection exception")
			self.log.exception(e)
			self.setup_cassandra(reinitialize=True)
		except Exception as e:
			self.log.error("IVAuthDBServer.check_auth_password request: unexpected exception")
			self.log.exception(e)

		return paramiko.AUTH_FAILED

	def check_channel_request(self, kind, channelId):
		""" Determine if a channel request will be granted, and return
		OPEN_SUCCEEDED or an error code. This method is called in
		server mode when the client requests a channel, after
		authentication is complete.

		By default this implementation returns OPEN_SUCCEEDED and then
		relies on the the default channel request handlers to manage
		the actual success or failure of the specific requests (almost
		all of which will be denied by default, with the exception of a
		request to open a subsystem matching a registered handler, such
		as the 'sftp' subsystem handler. """
		return paramiko.OPEN_SUCCEEDED
