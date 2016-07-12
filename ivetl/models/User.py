import uuid
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from django.contrib.auth.hashers import make_password as django_make_password
from django.contrib.auth.hashers import check_password as django_check_password
from ivetl.models import Publisher_User, PublisherMetadata


class Anonymous_User(object):
    user_id = ''
    email = ''
    staff = False
    superuser = False

    def is_anonymous(self):
        return True

    def is_authenticated(self):
        return False


class User(Model):
    user_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    email = columns.Text(index=True)
    password = columns.Text()
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

    @property
    def user_id_as_str(self):
        return str(self.user_id)

    def set_password(self, password):
        self.password = self.make_password(password)
        self.save()

    def check_password(self, password):
        return django_check_password(password, self.password)

    @staticmethod
    def make_password(password):
        return django_make_password(password)

    @staticmethod
    def slug_to_email(slug):
        return slug.replace('-at-', '@')

    def is_anonymous(self):
        return False

    def is_authenticated(self):
        return True

    def get_accessible_publishers(self):
        if self.superuser:
            return PublisherMetadata.objects.all()
        else:
            publisher_id_list = [p.publisher_id for p in Publisher_User.objects.filter(user_id=self.user_id)]
            return PublisherMetadata.objects.filter(publisher_id__in=publisher_id_list)
