$.widget("custom.listtableaualertspage", {
    options: {
        csrfToken: ''
    },

    _create: function () {
        var self = this;

        $('.delete-alert').click(function (event) {
            var button = $(this);
            var row = button.closest('tr');
            var alertId = button.attr('alert_id');
            var publisherId = button.attr('publisher_id');

            var m = $('#confirm-delete-alert-modal');

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
