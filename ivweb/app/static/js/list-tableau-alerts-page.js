$.widget("custom.listtableaualertspage", {
    options: {
        csrfToken: ''
    },

    _create: function () {
        var self = this;

        $('.alert-enabled-switch input[type="checkbox"]').on('click', function () {
            var enabledSwitch = $(this);
            var row = enabledSwitch.closest('tr');
            var alertId = row.attr('alert_id');
            var publisherId = row.attr('publisher_id');

            var data = {
                alert_id: alertId,
                publisher_id: publisherId,
                enabled: enabledSwitch.is(':checked') ? '1' : '',
                csrfmiddlewaretoken: self.options.csrfToken
            };

            $.post('/toggletableaualert/', data)
                .always(function () {
                    // check error messages?
                });
        });

        $('.delete-alert').on('click', function (event) {
            var button = $(this);
            var row = button.closest('tr');
            var alertId = row.attr('alert_id');
            var publisherId = row.attr('publisher_id');

            var m = $('#confirm-delete-alert-modal');

            m.find('.confirm-delete-question').html('Are you sure you want to delete the <b>' + row.attr('alert_name') + '</b> alert?');

            var submitButton = m.find('.confirm-delete-alert-button');
            submitButton.on('click', function () {
                button.hide();
                button.closest('tr').find('.alert-deleting-icon').show();

                submitButton.off('click');
                m.off('hidden.bs.modal');
                m.modal('hide');

                var data = {
                    alert_id: alertId,
                    publisher_id: publisherId,
                    expire_notifications: m.find('#id_expire_notifications').is(':checked') ? '1' : '',
                    csrfmiddlewaretoken: self.options.csrfToken
                };

                $.post('/deletetableaualert/', data)
                    .always(function () {
                        setTimeout(function () {
                            row.fadeOut(300, function () {
                                row.remove();
                            });
                        }, 1000)
                    });
            });

            var cancelButton = m.find('.cancel-delete-alert');
            cancelButton.on('click', function () {
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
