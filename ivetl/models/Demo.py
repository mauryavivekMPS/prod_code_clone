import uuid
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from ivetl.models import User
from ivetl.common import common


class Demo(Model):
    demo_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    name = columns.Text()
    requestor_id = columns.UUID(index=True)
    start_date = columns.DateTime()
    status = columns.Text()
    properties = columns.Text()
    archived = columns.Boolean(default=False, index=True)

    @property
    def requestor(self):
        return User.objects.get(user_id=self.requestor_id)

    @property
    def display_status(self):
        return common.DEMO_STATUS_LOOKUP.get(self.status)
