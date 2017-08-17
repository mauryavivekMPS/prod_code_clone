import uuid
import json
import re
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
    created = columns.DateTime()
    created_by = columns.UUID(index=True)

    def _clean_quantitative_filter_name(self, name):
        m = re.search('^.*\((.*)\)$', name)
        if m and len(m.groups()) == 1:
            return m.groups()[0]
        else:
            return name

    def _generate_dict_display_string(self, d):
        display_strings = []
        for n, v in d.items():
            filter_type = v['type']
            if filter_type == 'categorical':
                values = v['values']
                if type(values) == list:
                    value_string = ', '.join([str(each_v) for each_v in values])
                else:
                    value_string = str(values)
                exclude_string = ' (excluded)' if v['exclude'] else ''
                display_strings.append('%s%s = %s' % (n, exclude_string, value_string))
            elif filter_type == 'quantitative':
                display_strings.append('%s = %s to %s' % (self._clean_quantitative_filter_name(n), v['min'], v['max']))
        return ', '.join(display_strings)

    def _generate_dict_query_string(self, d):
        display_strings = []
        for n, v in d.items():
            filter_type = v['type']
            if filter_type == 'categorical':
                values = v['values']
                if type(values) == list:
                    value_string = ','.join([str(each_v) for each_v in values])
                else:
                    value_string = str(values)
                # TODO: add quant code here
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
        params_and_filters = {}
        params_and_filters.update(json.loads(self.alert_filters))
        params_and_filters.update(json.loads(self.alert_params))
        all_names = []
        for n, v in params_and_filters.items():
            if v['type'] == 'quantitative':
                all_names.append(self._clean_quantitative_filter_name(n))
            else:
                all_names.append(n)
        return ', '.join(all_names)

    @property
    def params_and_filters_query_string(self):
        params_and_filters = {}
        params_and_filters.update(json.loads(self.alert_filters))
        params_and_filters.update(json.loads(self.alert_params))
        return self._generate_dict_query_string(params_and_filters)

    @property
    def has_params(self):
        return self.alert_params and self.alert_params != '{}'

    @property
    def has_filters(self):
        return self.alert_filters and self.alert_filters != '{}'
