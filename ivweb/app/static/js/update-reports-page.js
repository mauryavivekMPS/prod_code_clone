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
            var itemId = row.attr('item_id');
            var itemType = row.attr('item_type');

            var publisherMenu = row.find('.inline-report-publisher-menu');
            var publisherId = publisherMenu.find("option:selected").val();
            var publisherName = publisherMenu.find("option:selected").text();
            if (!publisherId) {
                publisherName = 'all publishers';
            }

            var m = $('#confirm-update-report-modal');
            m.find('.modal-title').text('Update ' + itemType[0].toUpperCase() + itemType.slice(1));
            m.find('.modal-body').html('<p>Are you sure you want to update <b>' + itemId + '</b> for <b>' + publisherName + '</b>?');

            var submitButton = m.find('.confirm-update-report-button');
            submitButton.on('click', function() {
                row.find('.little-report-update-button').hide();
                row.find('.report-updating-icon').show();

                submitButton.off('click');
                m.off('hidden.bs.modal');
                m.modal('hide');

                IvetlWeb.showLoading();

                var data = {
                    'item_id': itemId,
                    'item_type': itemType,
                    'publisher_id': publisherId,
                    'csrfmiddlewaretoken': self.options.csrfToken
                };

                $.post('/updatereportitem/', data)
                    .always(function() {
                        IvetlWeb.hideLoading();
                    });
            });

            var cancelButton = m.find('.cancel-update-report');
            cancelButton.on('click', function() {
                $(this).off('click');
            });

            m.modal();

            m.on('hidden.bs.modal', function () {
                submitButton.off('click');
                m.off('hidden.bs.modal');
            });

            event.preventDefault();
        });

    }
});
