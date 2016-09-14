$.widget("custom.updatereportspage", {
    options: {
        csrfToken: ''
    },

    intervalId: null,

    _create: function() {
        var self = this;

        var allButtons = $('.little-report-update-button');
        this._wireReportUpdateButtons(allButtons);

        this.intervalId = setInterval(function() {
            $.get('/includereportitemstatuses/')
                .done(function(response) {
                    $.each(response.report_items, function(index, item) {
                        var row = $('tr[item_type="' + item.type + '"][item_id="' + item.id + '"]');
                        if (row.attr('item_status') != item.status) {
                            row.replaceWith(item.html);
                            var newRow = $('tr[item_type="' + item.type + '"][item_id="' + item.id + '"] .little-report-update-button');
                            self._wireReportUpdateButtons(newRow);
                        }
                    });
                });
        }, 2000);
    },

    _wireReportUpdateButtons: function(selector) {
        var self = this;
        selector.click(function(event) {
            var button = $(this);
            var row = button.closest('tr');

            row.find('.little-report-update-button').hide();
            row.find('.report-updating-icon').show();

            var data = {
                'item_id': row.attr('item_id'),
                'item_type': row.attr('item_type'),
                'csrfmiddlewaretoken': self.options.csrfToken
            };

            $.post('/updatereportitem/', data);

            event.preventDefault();
        });

    }
});
