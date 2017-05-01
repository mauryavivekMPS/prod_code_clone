import uuid
import json
import urllib.parse
from cassandra.cqlengine import columns
from cassandra.cqlengine.models import Model


class TableauAlert(Model):
    alert_id = columns.UUID(primary_key=True, default=uuid.uuid4)
    publisher_id = columns.Text(partition_key=True)
    name = columns.Text()
    template_id = columns.Text(primary_key=True)
    alert_params = columns.Text(default='{}')
    alert_filters = columns.Text(default='{}')
    attachment_only_emails = columns.List(columns.Text())
    full_emails = columns.List(columns.Text())
    custom_message = columns.Text()
    send_with_no_data = columns.Boolean()
    enabled = columns.Boolean()
    archived = columns.Boolean(index=True)

    def _generate_dict_display_string(self, d):
        display_strings = []
        for n, v in d.items():
            if type(v) == list:
                value_string = ', '.join(v)
            else:
                value_string = v
            display_strings.append('%s = %s' % (n, value_string))
        return ', '.join(display_strings)

    def _generate_dict_query_string(self, d):
        display_strings = []
        for n, v in d.items():
            if type(v) == list:
                value_string = ','.join(v)
            else:
                value_string = v
            display_strings.append('%s=%s' % (urllib.parse.quote(n), urllib.parse.quote(value_string)))
        return '&'.join(display_strings)

    @property
    def params_display_string(self):
        params = json.loads(self.alert_params)
        return self._generate_dict_display_string(params)

    @property
    def filters_display_string(self):
        filters = json.loads(self.alert_filters)
        return self._generate_dict_display_string(filters)

    @property
    def params_and_filters_display_string(self):
        params_and_filters = {}
        params_and_filters.update(json.loads(self.alert_filters))
        params_and_filters.update(json.loads(self.alert_params))
        return self._generate_dict_display_string(params_and_filters)

    @property
    def params_and_filters_names_string(self):
        params_and_filters = []
        params_and_filters.extend(json.loads(self.alert_filters).keys())
        params_and_filters.extend(json.loads(self.alert_params).keys())
        return ', '.join(params_and_filters)

    @property
    def params_and_filters_query_string(self):
        params_and_filters = {}
        params_and_filters.update(json.loads(self.alert_filters))
        params_and_filters.update(json.loads(self.alert_params))
        # return urllib.parse.urlencode(params_and_filters, quote_via=urllib.parse.quote)
        return self._generate_dict_query_string(params_and_filters)

    @property
    def has_params(self):
        return self.alert_params and self.alert_params != '{}'

    @property
    def has_filters(self):
        return self.alert_filters and self.alert_filters != '{}'
