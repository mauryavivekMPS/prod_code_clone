from cassandra.cqlengine.models import Model


class IvetlModel(Model):
    __abstract__ = True

    tableau_filter_replacement_characters = {
        ',': ';',
        '?': '#',
    }

    tableau_filter_fields = []

    def clean_tableau_filter_value(self, s):
        if s:
            for a, b in self.tableau_filter_replacement_characters.items():
                s = s.replace(a, b)
        return s

    def clean_all_tableau_filter_fields(self):
        for field in self.tableau_filter_fields:
            cleaned_value = self.clean_tableau_filter_value(getattr(self, field))
            setattr(self, field, cleaned_value)

    def validate(self):
        self.clean_all_tableau_filter_fields()
        super(IvetlModel, self).validate()
