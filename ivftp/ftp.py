#!/usr/bin/env python

import os
os.sys.path.append(os.environ['IVETL_ROOT'])

import re
from pyftpdlib.authorizers import DummyAuthorizer, AuthenticationFailed
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
from ivetl.models import User, Publisher_User, Publisher_Metadata
from ivetl.celery import open_cassandra_connection, close_cassandra_connection
from ivetl.common import common

BASE_INCOMING_DIR = '/iv/incoming'


class IvetlAuthorizer(DummyAuthorizer):

    def validate_authentication(self, username, password, handler):
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            raise AuthenticationFailed

        if user.check_password(password):
            if user.superuser:
                home_dir = BASE_INCOMING_DIR
            elif user.staff:
                # TODO: need to figure out how to handle multiple accounts
                pass
            else:
                # users can only see their pub directory
                accessible_publishers = user.get_accessible_publishers()
                if not accessible_publishers:
                    raise AuthenticationFailed

                # TODO: need to figure out how to handle mutiple accounts

                home_dir = os.path.join(BASE_INCOMING_DIR, accessible_publishers[0].publisher_id)

            # add the user on-demand so that the rest of the class behaves normally
            self.add_user(user.email, '', home_dir, perm='elradfmw')

            return True
        else:
            raise AuthenticationFailed


class IvetlHandler(FTPHandler):

    def on_file_received(self, file):
        # get the pipeline from the path
        pipeline_id = ''
        publisher_id = ''

        m = re.search('.*/(\w+)/(\w+)/.*$', file)
        if m and len(m.groups()) == 2:
            publisher_id, pipeline_id = m.groups()
            pipeline = common.PIPELINE_BY_ID[pipeline_id]

            print('running: %s for %s' % (pipeline['name'], publisher_id))

        # TODO: will there be a problem distinguishing cohort or not here?


def main():

    # initialize the database
    open_cassandra_connection()

    authorizer = IvetlAuthorizer()
    handler = IvetlHandler
    handler.authorizer = authorizer
    handler.banner = "Impact Vizor ftpd ready."
    address = ('', 2121)
    server = FTPServer(address, handler)
    server.max_cons = 256
    server.max_cons_per_ip = 5
    server.serve_forever()

    # clean up
    close_cassandra_connection()

if __name__ == '__main__':
    main()
