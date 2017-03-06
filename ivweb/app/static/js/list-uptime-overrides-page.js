$.widget("custom.listuptimeoverridespage", {
    options: {
        csrfToken: ''
    },

    _create: function() {
        var self = this;

        $('.delete-override').click(function(event) {
            var button = $(this);
            var row = button.closest('tr');
            var overrideId = button.attr('override_id');
            var overrideLabel = button.attr('override_label');
            var overrideDateRange = button.attr('override_date_range');

            var m = $('#confirm-delete-override-modal');
            m.find('.override-label').text(overrideLabel);
            m.find('.override-date-range').text(overrideDateRange);

            var submitButton = m.find('.confirm-delete-override-button');
            submitButton.on('click', function() {
                button.hide();
                button.closest('tr').find('.override-deleting-icon').show();

                submitButton.off('click');
                m.off('hidden.bs.modal');
                m.modal('hide');

                var data = {
                    override_id: overrideId,
                    csrfmiddlewaretoken: self.options.csrfToken
                };

                $.post('/deleteuptimeoverride/', data)
                    .always(function() {
                        setTimeout(function() {
                            row.fadeOut(300, function() {
                                row.remove();
                            });
                        }, 1000)
                    });
            });

            var cancelButton = m.find('.cancel-delete-override');
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
