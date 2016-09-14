$.widget("custom.updatereportspage", {
    options: {
        csrfToken: ''
    },

    intervalId: null,

    _create: function() {
        var self = this;

        $('.little-report-update-button').click(function(event) {
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

        this.intervalId = setInterval(function() {


        }, 2000);
    }
});
