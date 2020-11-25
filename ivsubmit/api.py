import atexit
import datetime
import html
import logging
import os
import re
import threading

from collections import defaultdict
from django.core.urlresolvers import reverse
from ivetl.celery import open_cassandra_connection, close_cassandra_connection
from ivetl.common import common
from ivetl import utils
from ivetl.models import User, UploadedFile
from ivweb.app.views.pipelines import move_invalid_file_to_cold_storage


class PipelineSubmitter:
	def __init__(self, email, notify=False, log=None):
		"""
		PipelineSubmitter is initialized for a user (identified by
		email), and manages the validation, rejection, or submission of
		filepaths into the IV pipelines.  If notify is True then any
		validation errors will trigger the sending of an email to the
		user describing the error.
		"""
		open_cassandra_connection()
		atexit.register(close_cassandra_connection)

		self.user = User.objects.get(email=email)
		self.notify = notify
		self.validated = defaultdict(dict)
		self.log = log

		# self.lock guards access to self.validated
		self.lock = threading.Lock()

		# if no logger was passed in, create a default one
		if self.log is None:
			handler = logging.StreamHandler()
			handler.setFormatter(logging.Formatter(
				fmt='%(asctime)s %(levelname)s %(name)s %(filename)s:%(lineno)s %(message)s',
				datefmt='%Y-%m-%dT%H:%M:%S%z'))
			self.log = logging.getLogger(__name__)
			self.log.addHandler(handler)

	def add(self, filepath):
		"""
		add validates a filepaht and, if it passes, queues the file for
		submission.  If a filepath fails validation and the
		PipelineSubmitted was initialized with notify True, an email
		will be sent to the user indicating the problem.

		Once all the files for the user have been added, the submit
		function should be called to submit them to the ETL pipeline.
		"""
		now = datetime.datetime.now()
		publisher_id, pipeline_ftp_dir = self._parse_filepath(filepath)
		if publisher_id is None or pipeline_ftp_dir is None:
			return False

		filename = os.path.basename(filepath)
		product_id = common.PRODUCT_ID_BY_FTP_DIR_NAME[pipeline_ftp_dir]
		pipeline_id = common.PIPELINE_ID_BY_FTP_DIR_NAME[pipeline_ftp_dir]
		pipeline = common.PIPELINE_BY_ID[pipeline_id]

		if pipeline.get('validator_class'):
			self.log.info("Validating file: %s" % filename)

			validator_class = common.get_validator_class(pipeline)
			validator = validator_class()

			count, raw_errors = validator.validate_files([filepath], publisher_id=publisher_id)
			errors = validator.parse_errors(raw_errors)
			if errors:
				self._rejected(filepath, errors)
				return False
		else:
			self.log.info("no validator specified for pipeline: %s" % pipeline)

		try:
			os.chmod(filepath, 0o664)
			self.log.info("Validated file and successfully applied chmod 0664: %s" % filename)
		except Exception as e:
			self.log.error("Validated file but failed to chmod 0664: %s: %s" % (filename, e))
			return False

		UploadedFile.objects.create(
			publisher_id=publisher_id,
			processed_time=now,
			product_id='ftp',
			pipeline_id='upload',
			job_id='',
			path=filepath,
			user_id=self.user.user_id,
			original_name=filename,
			validated=True,
		)

		utils.add_audit_log(
			user_id=self.user.user_id,
			publisher_id=publisher_id,
			action='ftp-file',
			description='Valid uploaded %s FTP/SFTP file: %s' % (pipeline['id'], filename),
		)

		with self.lock:
			publisher_queue = self.validated[publisher_id]
			if pipeline_ftp_dir not in publisher_queue:
				file_queue = {
					'product_id': product_id,
					'pipeline': pipeline,
					'files': []
				}
				publisher_queue[pipeline_ftp_dir] = file_queue
			else:
				file_queue = publisher_queue[pipeline_ftp_dir]

			file_queue['files'].append(filepath)

		return True

	def count(self):
		"""
		count returns the number of validated filepath queued for submission
		"""
		n = 0
		with self.lock:
			for publisher_id, publisher_queue in self.validated.items():
				for pipeline_ftp_dir, file_queue in publisher_queue.items():
					n += 1
		return n

	def submit(self):
		"""
		submit validated files into the ETL pipeline queue
		"""

		with self.lock:
			validated = self.validated
			self.validated = defaultdict(dict)

		n = 0
		for publisher_id, publisher_queue in validated.items():
			for pipeline_ftp_dir, file_queue in publisher_queue.items():
				product_id = file_queue['product_id']
				pipeline = file_queue['pipeline']
				files = file_queue['files']

				pipeline_class = common.get_pipeline_class(pipeline)

				pipeline_class.s(
					publisher_id_list=[publisher_id],
					product_id=product_id,
					files=files,
					preserve_incoming_files=True,
					initiating_user_email=self.user.email,
				).delay()

				utils.add_audit_log(
					user_id=self.user.user_id,
					publisher_id=publisher_id,
					action='run-pipeline',
					description='Run pipeline from FTP/SFTP: %s' % (pipeline['id']),
				)

				n += 1
		return n

	def _parse_filepath(self, filepath):
		"""
		Given a filepath return the prior directory components
		publisher_id (grandparent), and pipeline_ftp_dir (parent).  If
		either of the components is missing, None is returned for both
		values. If a match is made then it is expected that the
		pipeline_ftp_dir can be resolved to a product_id and
		pipeline_id via the ivetl.commons PRODUCT_ID_BY_FTP_DIR_NAME
		and PIPELINE_ID_BY_FTP_DIR_NAME maps respectively.
		"""
		publisher_id = None
		pipeline_ftp_dir = None

		m = re.search(r'/([^/]+)/([^/]+)/[^/]+$', filepath)
		if m and len(m.groups()) == 2:
			publisher_id, pipeline_ftp_dir = m.groups()
		return publisher_id, pipeline_ftp_dir

	def _rejected(self, filepath, errors):
		"""
		Send an email to the user informing them of the failure of
		filepath to validate, including any error details available,
		migrate the file to the invalid files workspace, and add an
		audit record for the filepath.
		"""
		now = datetime.datetime.now()
		publisher_id, pipeline_ftp_dir = self._parse_filepath(filepath)
		if publisher_id is None or pipeline_ftp_dir is None:
			return

		filename = os.path.basename(filepath)
		product_id = common.PRODUCT_ID_BY_FTP_DIR_NAME[pipeline_ftp_dir]
		pipeline_id = common.PIPELINE_ID_BY_FTP_DIR_NAME[pipeline_ftp_dir]
		pipeline = common.PIPELINE_BY_ID[pipeline_id]

		subj = "Impact Vizor (%s): Problems processing your %s file" % (publisher_id, pipeline['user_facing_file_description'])
		body = "<p>We found some validation errors in: <b>%s</b></p>" % (html.escape(filename))
		body += "<ul>"
		for error in errors:
			body += "<li>Line %s: %s</i>" % (error['line_number'], html.escape(error['message']))
		body += "</ul>"
		body += "<p>Please resolve the errors above and submit the file again.</p>"
		body += "<p>Thank you,<br/>Impact Vizor Team</p>"

		if self.notify:
			common.send_email(subj, body, to=self.user.email, bcc=common.FTP_ADMIN_BCC)
		else:
			msg = [
				"PipelineSubmitted email generated, but not sent:",
				"FROM %s %s" % (common.EMAIL_FROM, now.strftime("%a %b %-d %H:%M:%S %Y")),
				"From: %s" % (common.EMAIL_FROM),
				"To: %s" % (self.user.email),
				"Bcc: %s" % (common.FTP_ADMIN_BCC),
				"Subject: %s" % (subj),
				"",
				body.replace("\nFrom ", "\n>From "),
			]
			self.log.info("\n".join(msg))

		new_path = move_invalid_file_to_cold_storage(filepath, publisher_id, product_id, pipeline_id, now)
		uploaded_file_record = UploadedFile.objects.create(
			publisher_id=publisher_id,
			processed_time=now,
			product_id='ftp',
			pipeline_id='upload',
			job_id='',
			path=new_path,
			user_id=self.user.user_id,
			original_name=filename,
			validated=False,
		)

		self.log.warn("Validation failed for %s with %s errors, archiving to %s" % (filename, len(errors), new_path))

		file_viewer_url = reverse('uploaded_files.download', kwargs={
			'publisher_id': publisher_id,
			'uploaded_file_id': uploaded_file_record.uploaded_file_id,
		})

		new_file_link = '<a class="external-link" href="%s">%s</a>' % (file_viewer_url, filename)
		utils.add_audit_log(
			user_id=self.user.user_id,
			publisher_id=publisher_id,
			action='ftp-file-invalid',
			description='Invalid FTP upload %s file: %s' % (pipeline['id'], new_file_link),
		)
