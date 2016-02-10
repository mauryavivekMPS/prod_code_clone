import uuid
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model
from ivetl.models import User


class Demo(Model):
    demo_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    name = columns.Text()
    requestor_id = columns.UUID(index=True)
    start_date = columns.DateTime()
    status = columns.Text()
    properties = columns.Text()

    @property
    def requestor(self):
        return User.objects.get(user_id=self.requestor_id)
