from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class User(Model):
    email = columns.Text(primary_key=True)
    first_name = columns.Text()
    last_name = columns.Text()
    staff = columns.Boolean()
    superuser = columns.Boolean()

    @property
    def display_name(self):
        if self.first_name and self.last_name:
            return '%s %s' % (self.first_name, self.last_name)
        else:
            return self.email

    @property
    def slug(self):
        return self.email.replace('@', '-at-')

    @staticmethod
    def slug_to_email(slug):
        return slug.replace('-at-', '@')
