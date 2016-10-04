import uuid
import json
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class UptimeOverride(Model):
    override_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    label = columns.Text()
    start_date = columns.DateTime()
    end_date = columns.DateTime()
    match_expression_json = columns.Text()
    override_type = columns.Text()
    applied_date = columns.DateTime()
    notes = columns.Text()

    @property
    def display_match_expression(self):
        bits = []
        match_expression = json.loads(self.match_expression_json)
        for filter_id, values in match_expression.items():
            if values:
                bits.append('%s = %s' % (filter_id, ", ".join(values)))
        return " + ".join(bits)
