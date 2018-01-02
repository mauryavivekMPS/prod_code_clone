import uuid
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from django.contrib.auth.hashers import make_password as django_make_password
from django.contrib.auth.hashers import check_password as django_check_password
from ivetl.models import PublisherUser, PublisherMetadata


class AnonymousUser(object):
    user_id = ''
    email = ''
    staff = False
    superuser = False

    def is_anonymous(self):
        return True

    def is_authenticated(self):
        return False

    @property
    def is_publisher_ftp(self):
        return False

    @property
    def is_publisher_staff(self):
        return False

    @property
    def is_highwire_staff(self):
        return False

    @property
    def is_superuser(self):
        return False

    @property
    def is_at_least_publisher_ftp_only(self):
        return False

    @property
    def is_at_least_publisher_staff(self):
        return False

    @property
    def is_at_least_highwire_staff(self):
        return False


class User(Model):
    user_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    email = columns.Text(index=True)
    password = columns.Text()
    first_name = columns.Text()
    last_name = columns.Text()
    user_type = columns.Integer()

    # 10 publisher ftp only
    # 20 publisher staff
    # 30 highwire stff
    # 40 superuser

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
        if self.is_superuser:
            return PublisherMetadata.objects.all()
        else:
            publisher_id_list = [p.publisher_id for p in PublisherUser.objects.filter(user_id=self.user_id)]
            return PublisherMetadata.objects.filter(publisher_id__in=publisher_id_list)

    @property
    def is_publisher_ftp(self):
        return self.user_type == 10

    @property
    def is_publisher_staff(self):
        return self.user_type == 20

    @property
    def is_highwire_staff(self):
        return self.user_type == 30

    @property
    def is_superuser(self):
        return self.user_type == 40

    @property
    def is_at_least_publisher_ftp_only(self):
        return self.user_type >= 10

    @property
    def is_at_least_publisher_staff(self):
        return self.user_type >= 20

    @property
    def is_at_least_highwire_staff(self):
        return self.user_type >= 30
