$.widget("custom.editvaluemappingspage", {
    options: {
        publisherId: '',
        mappingType: '',
        csrfToken: ''
    },

    _create: function () {
        var self = this;

        $('.edit-display-value-link[data-toggle="popover"]').popover({
            html: true,
            title: 'Enter a new display value',
            content: function () {
                return $(this).closest('.mapping-header').find('.edit-display-popover').html();
            }
        });

        $('.mapping-container').on('click', '.popover .edit-display-button', function () {
            var mappingContainer = $(this).closest('.mapping-container');
            var canonicalValue = mappingContainer.attr('canonical_value');
            var textbox = mappingContainer.find('.edit-display-textbox');
            var newDisplayValue = textbox.val();

            IvetlWeb.showLoading();

            var data = {
                'publisher_id': self.options.publisherId,
                'mapping_type': self.options.mappingType,
                'canonical_value': canonicalValue,
                'display_value': newDisplayValue,
                'csrfmiddlewaretoken': self.options.csrfToken
            };

            $.post('/updatevaluedisplay/', data)
                .always(function () {
                    mappingContainer.find('.display-value').text(newDisplayValue);
                    IvetlWeb.hideLoading();
                });

        });
    }
});
