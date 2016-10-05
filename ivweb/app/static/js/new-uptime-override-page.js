$.widget("custom.newuptimeoverridepage", {
    options: {
        filters: []
    },

    _create: function() {
        var self = this;

        $('#id_start_date').datepicker({
            autoclose: true
        });
        $('#id_end_date').datepicker({
            autoclose: true
        });

        $('.new-uptime-override-form').on('submit', function(event) {
            var matchExpression = {};
            $.each(self.options.filters, function(index, filter) {
                var values = $.map($('#id_filter_' + filter).val().split(','), function(s) {
                    var trimmedValue = s.trim();
                    if (trimmedValue != '') {
                        return trimmedValue;
                    }
                    return null;
                });
                matchExpression[filter] = values;
            });
            $('#id_match_expression_json').val(JSON.stringify(matchExpression));
        });
    }
});
