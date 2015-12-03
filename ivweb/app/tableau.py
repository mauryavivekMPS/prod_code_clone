import untangle
import requests


class TableauClient(object):

    def __init__(self, username='admin', password='admin', server='http://10.0.0.143'):
        self.username = username
        self.password = password
        self.server = server
        self.token = ''
        self.user_id = ''
        self.site_id = ''

    def sign_in(self):
        url = self.server + "/api/2.0/auth/signin"

        request_string = """
            <tsRequest>
              <credentials name="%s" password="%s" >
                <site contentUrl="" />
              </credentials>
            </tsRequest>
        """

        response = requests.post(url, data=request_string % (self.username, self.password))
        if response.status_code != 200:
            print('There was an error:')
            print(response.text)

        r = untangle.parse(response.text).tsResponse
        self.token = r.credentials['token']
        self.site_id = r.credentials.site['id']
        self.user_id = r.credentials.user['id']

        print('The token is: %s' % self.token)

    def create_project(self, project_name):
        url = self.server + "/api/2.0/sites/%s/projects" % self.site_id

        request_string = """
            <tsRequest>
              <project name="%s" />
            </tsRequest>
        """

        response = requests.post(url, data=request_string % project_name, headers={'X-Tableau-Auth': self.token})
        if response.status_code != 201:
            print('There was an error:')
            print(response.text)

        r = untangle.parse(response.text).tsResponse
        project_id = r.project['id']
        print('The new project ID is: %s' % project_id)
        return project_id

    def create_group(self, group_name):
        url = self.server + "/api/2.0/sites/%s/groups" % self.site_id

        request_string = """
            <tsRequest>
              <group name="%s" />
            </tsRequest>
        """

        response = requests.post(url, data=request_string % group_name, headers={'X-Tableau-Auth': self.token})
        if response.status_code != 201:
            print('There was an error:')
            print(response.text)

        r = untangle.parse(response.text).tsResponse
        group_id = r.group['id']

        print('The new group ID is: %s' % group_id)
        return group_id

    def add_group_to_project(self, group_id, project_id):
        url = self.server + "/api/2.0/sites/%s/projects/%s/permissions" % (self.site_id, project_id)

        request_string = """
            <tsRequest>
                <permissions>
                    <project id="%s" />
                    <granteeCapabilities>
                        <group id="%s" />
                        <capabilities>
                            <capability name="Connect" mode="Allow" />
                            <capability name="Read" mode="Allow" />
                            <capability name="Filter" mode="Allow" />
                            <capability name="ViewUnderlyingData" mode="Allow" />
                            <capability name="ExportData" mode="Allow" />
                            <capability name="ExportImage" mode="Allow" />
                        </capabilities>
                    </granteeCapabilities>
                </permissions>
            </tsRequest>
        """

        response = requests.put(url, data=request_string % (project_id, group_id), headers={'X-Tableau-Auth': self.token})
        if response.status_code != 200:
            print('There was an error:')
            print(response.text)

    def create_user(self, username):
        url = self.server + "/api/2.0/sites/%s/users" % self.site_id

        request_string = """
            <tsRequest>
                <user name="%s" siteRole="Interactor" />
            </tsRequest>
        """

        response = requests.post(url, data=request_string % username, headers={'X-Tableau-Auth': self.token})
        if response.status_code != 201:
            print('There was an error:')
            print(response.text)

        r = untangle.parse(response.text).tsResponse
        user_id = r.user['id']

        print('The new user ID is: %s' % user_id)
        return user_id

    def set_user_password(self, user_id, password):
        url = self.server + "/api/2.0/sites/%s/users/%s" % (self.site_id, user_id)

        request_string = """
            <tsRequest>
                <user password="%s" />
            </tsRequest>
        """

        response = requests.put(url, data=request_string % password, headers={'X-Tableau-Auth': self.token})
        if response.status_code != 200:
            print('There was an error:')
            print(response.text)

    def add_user_to_group(self, user_id, group_id):
        url = self.server + "/api/2.0/sites/%s/groups/%s/users/" % (self.site_id, group_id)

        request_string = """
            <tsRequest>
                <user id="%s" />
            </tsRequest>
        """

        response = requests.post(url, data=request_string % user_id, headers={'X-Tableau-Auth': self.token})
        if response.status_code != 200:
            print('There was an error:')
            print(response.text)

    def setup_account(self, project_name, username, password):
        self.sign_in()
        project_id = self.create_project(project_name)
        group_id = self.create_group(project_name)
        self.add_group_to_project(group_id, project_id)
        user_id = self.create_user(username)
        self.set_user_password(user_id, password)
        self.add_user_to_group(user_id, group_id)

