#!/usr/bin/env python

import os
os.sys.path.append(os.environ['IVETL_ROOT'])

import re
import datetime
import stat
from collections import defaultdict
from pyftpdlib.authorizers import DummyAuthorizer, AuthenticationFailed
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
from ivetl.celery import open_cassandra_connection, close_cassandra_connection
from ivetl.common import common
from ivetl.models import Publisher_Metadata, User, Audit_Log


class IvetlAuthorizer(DummyAuthorizer):

    def validate_authentication(self, username, password, handler):
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            raise AuthenticationFailed

        if user.check_password(password):
            if user.superuser:
                accessible_publishers = Publisher_Metadata.objects.all()
            else:
                accessible_publishers = user.get_accessible_publishers()

            user_dir_name = user.email.replace('@', '_').replace('.', '_')
            for publisher in accessible_publishers:
                for product_id in publisher.supported_products:
                    product = common.PRODUCT_BY_ID[product_id]
                    if not product['cohort']:
                        for pipeline in [p['pipeline'] for p in product['pipelines']]:
                            if pipeline.get('has_file_input'):
                                ftp_dir_name = common.get_ftp_dir_name(product_id, pipeline['id'])
                                os.makedirs(os.path.join(common.BASE_FTP_DIR, user_dir_name, publisher.publisher_id, ftp_dir_name), exist_ok=True)

            home_dir = os.path.join(common.BASE_FTP_DIR, user_dir_name)

            # add the user on-demand so that the rest of the class behaves normally
            if not self.has_user(user.email):
                self.add_user(user.email, '', home_dir, perm='elrw')

            return True
        else:
            raise AuthenticationFailed


class IvetlHandler(FTPHandler):

    def __init__(self, conn, server, ioloop=None):
        super(IvetlHandler, self).__init__(conn, server, ioloop)
        self.uploaded_files = []

    def on_file_received(self, file):
        self.uploaded_files.append(file)

    def on_disconnect(self):
        """Called when connection is closed."""

        files_to_process = defaultdict(dict)  # indexed by pub then by ftp_dir_name

        user = User.objects.get(email=self.username)

        for file in self.uploaded_files:
            file_name = os.path.basename(file)

            # get the pipeline and publisher from the path
            m = re.search('.*/(\w+)/(\w+)/.*$', file)
            if m and len(m.groups()) == 2:
                publisher_id, pipeline_ftp_dir_name = m.groups()
                product_id = common.PRODUCT_ID_BY_FTP_DIR_NAME[pipeline_ftp_dir_name]
                pipeline_id = common.PIPELINE_ID_BY_FTP_DIR_NAME[pipeline_ftp_dir_name]
                pipeline = common.PIPELINE_BY_ID[pipeline_id]

                # get the validator class, if any, and run validation
                if pipeline.get('validator_class'):
                    validator_class = common.get_validator_class(pipeline)
                    validator = validator_class()
                    line_count, raw_errors = validator.validate_files([file], publisher_id)
                    validation_errors = validator.parse_errors(raw_errors)

                    if validation_errors:
                        subject = "Impact Vizor (%s): Problems processing your %s file" % (publisher_id, common.get_pipeline_display_name(pipeline))
                        body = "<p>We found some validation errors in: <b>%s</b></p>" % file_name
                        body += "<ul>"
                        for error in validation_errors:
                            body += "<li>Line %s: %s</li>" % (error['line_number'], error['message'])
                        body += "</ul>"
                        body += "<p>Please resolve the errors above and FTP the file again.</p>"
                        body += '<p>Thank you,<br/>Impact Vizor Team</p>'
                        common.send_email(subject, body, to=user.email)

                        print('Validation failed for %s with %s errors' % (file_name, len(validation_errors)))

                        continue

                os.chmod(file, stat.S_IROTH | stat.S_IRGRP | stat.S_IWGRP | stat.S_IRUSR | stat.S_IWUSR)

                files_by_publisher = files_to_process[publisher_id]
                if pipeline_ftp_dir_name not in files_by_publisher:
                    files_by_publisher[pipeline_ftp_dir_name] = {
                        'product_id': product_id,
                        'pipeline': pipeline,
                        'files': []
                    }

                files_by_publisher[pipeline_ftp_dir_name]['files'].append(file)

        for publisher_id, files_by_pipeline in files_to_process.items():
            for pipeline_ftp_dir_name, pipeline_files in files_by_pipeline.items():

                product_id = pipeline_files['product_id']
                pipeline = pipeline_files['pipeline']
                files = pipeline_files['files']

                # kick the pipeline off with an explicit file list
                pipeline_class = common.get_pipeline_class(pipeline)
                pipeline_class.s(
                    publisher_id_list=[publisher_id],
                    product_id=product_id,
                    files=files,
                    preserve_incoming_files=True,
                    initiating_user_email=user.email,
                ).delay()

                Audit_Log.objects.create(
                    user_id=user.user_id,
                    event_time=datetime.datetime.now(),
                    action='run-pipeline',
                    entity_type='pipeline',
                    entity_id=pipeline['id'],
                )

if __name__ == '__main__':
    # initialize the database
    open_cassandra_connection()

    # initialize the server
    authorizer = IvetlAuthorizer()
    handler = IvetlHandler
    handler.authorizer = authorizer
    handler.banner = "Impact Vizor ftpd ready."
    handler.passive_ports=range(57000,57501)
    handler.masquerade_address = common.FTP_PUBLIC_IP
    address = ('', 2121)
    server = FTPServer(address, handler)
    server.max_cons = 256
    server.max_cons_per_ip = 5

    # start the server
    server.serve_forever()

    # clean up
    close_cassandra_connection()
