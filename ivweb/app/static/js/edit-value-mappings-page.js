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
            container: '#edit-value-mappings-page',
            content: function () {
                return $(this).closest('.mapping-container').find('.edit-display-popover').html();
            }
        }).on('show.bs.popover', function () {
            var mappingContainer = $(this).closest('.mapping-container');
            var canonicalValue = $(this).closest('.mapping-container').attr('canonical_value');
            var editContainer = $('.edit-display-container[canonical_value="' + canonicalValue + '"]');
            editContainer.find('.edit-display-textbox').val(mappingContainer.find('.display-value').text());
        });

        $('.edit-mapping-link[data-toggle="popover"]').popover({
            html: true,
            title: 'Choose a new mapping',
            container: '#edit-value-mappings-page',
            content: function () {
                return $(this).closest('.mapping-entry-container').find('.edit-mapping-popover').html();
            }
        });

        $('.show-mappings-link').on('click', function () {
            var mappingContainer = $(this).closest('.mapping-container');
            mappingContainer.find('.mapping-table').toggle();
        });

        $('#edit-value-mappings-page').on('click', '.popover .edit-display-button', function (event) {
            var editContainer = $(event.target).closest('.edit-display-container');
            var canonicalValue = editContainer.attr('canonical_value');
            var textbox = editContainer.find('.edit-display-textbox');
            var newDisplayValue = textbox.val();

            IvetlWeb.showLoading();

            var data = {
                'publisher_id': self.options.publisherId,
                'mapping_type': self.options.mappingType,
                'canonical_value': canonicalValue,
                'display_value': newDisplayValue,
                'csrfmiddlewaretoken': self.options.csrfToken
            };

            var mappingContainer = $('.mapping-container[canonical_value="' + canonicalValue + '"]');

            $.post('/updatevaluedisplay/', data)
                .done(function () {
                    mappingContainer.find('.display-value').text(newDisplayValue);
                    mappingContainer.find('.edit-display-value-link').popover('hide');
                    IvetlWeb.hideLoading();
                });

        });

        $('.mapping-container').on('click', '.popover .edit-mapping-button', function () {
            var mappingContainer = $(this).closest('.mapping-container');
            var canonicalValue = mappingContainer.attr('canonical_value');
            var textbox = mappingContainer.find('.edit-mapping-textbox');
            // var newDisplayValue = textbox.val();
            //
            // IvetlWeb.showLoading();
            //
            // var data = {
            //     'publisher_id': self.options.publisherId,
            //     'mapping_type': self.options.mappingType,
            //     'canonical_value': canonicalValue,
            //     'display_value': newDisplayValue,
            //     'csrfmiddlewaretoken': self.options.csrfToken
            // };
            //
            // $.post('/updatevaluedisplay/', data)
            //     .always(function () {
            //         mappingContainer.find('.display-value').text(newDisplayValue);
            //         IvetlWeb.hideLoading();
            //     });
        });
    }
});
