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

            $.post('/togglealert/', data)
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

                $.post('/deletealert/', data)
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

        $('.send-alert-now').on('click', function (event) {
            var button = $(this);
            var row = button.closest('tr');
            var alertId = row.attr('alert_id');
            var publisherId = row.attr('publisher_id');
            var fullEmails = row.attr('full_emails');
            var attachmentOnlyEmails = row.attr('attachment_only_emails');
            var customMessage = row.attr('custom_message');

            var m = $('#confirm-send-alert-now-modal');

            var fullEmailsTextarea = m.find('textarea[name="full_emails"]');
            var attachmentOnlyEmailsTextarea = m.find('textarea[name="attachment_only_emails"]');
            var customMessageTextarea = m.find('textarea[name="custom_message"]');

            fullEmailsTextarea.val(fullEmails);
            attachmentOnlyEmailsTextarea.val(attachmentOnlyEmails);
            customMessageTextarea.val(customMessage);

            var submitButton = m.find('.confirm-send-alert-now-button');
            submitButton.on('click', function () {
                button.hide();

                var sendingNowIcon = button.closest('tr').find('.alert-sending-now-icon');
                sendingNowIcon.show();

                submitButton.off('click');
                m.off('hidden.bs.modal');
                m.modal('hide');

                var data = {
                    alert_id: alertId,
                    publisher_id: publisherId,
                    full_emails: fullEmailsTextarea.val(),
                    attachment_only_emails: attachmentOnlyEmailsTextarea.val(),
                    custom_message: customMessageTextarea.val(),
                    csrfmiddlewaretoken: self.options.csrfToken
                };

                $.post('/sendalertnow/', data)
                    .always(function () {
                        setTimeout(function () {
                            sendingNowIcon.hide();
                            button.show();
                        }, 3000)
                    });
            });

            var cancelButton = m.find('.cancel-send-alert-now');
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
