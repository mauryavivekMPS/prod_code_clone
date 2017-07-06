$.widget("custom.editvaluemappingspage", {
    options: {
        publisherId: '',
        mappingType: '',
        csrfToken: ''
    },

    _create: function () {
        var self = this;

        //
        // wire up edit display popover
        //

        $('.edit-display-value-link').popover({
            html: true,
            title: 'Enter a new display value',
            container: '#edit-value-mappings-page',
            content: function () {
                return $(this).closest('.mapping-container').find('.edit-display-popover').html();
            }
        }).on('inserted.bs.popover', function () {
            var editLink = $(this);
            editLink.addClass('stay-visible');
            var mappingContainer = $(this).closest('.mapping-container');
            var canonicalValue = $(this).closest('.mapping-container').attr('canonical_value');
            var editContainer = $('.popover .edit-display-container[canonical_value="' + canonicalValue + '"]');
            editContainer.find('.edit-display-textbox').val(mappingContainer.find('.display-value').text());
            editContainer.find('.cancel-edit-display-button').on('click', function () {
                editLink.popover('hide');
            });
        }).on('hidden.bs.popover', function () {
            $(this).removeClass('stay-visible');
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

        //
        // wire up edit mapping popover
        //

        // $('.edit-mapping-link[data-toggle="popover"]').popover({
        //     html: true,
        //     title: 'Choose a new mapping',
        //     container: '#edit-value-mappings-page',
        //     content: function () {
        //         return $(this).closest('.mapping-entry-container').find('.edit-mapping-popover').html();
        //     }
        // });

        $('.edit-mapping-link').popover({
            html: true,
            title: 'Choose a new mapping',
            container: '#edit-value-mappings-page',
            content: function () {
                return $(this).closest('.mapping-container').find('.edit-mapping-popover').html();
            }
        }).on('inserted.bs.popover', function () {
            var editLink = $(this);
            editLink.addClass('stay-visible');
            var mappingEntryContainer = $(this).closest('.mapping-entry-container');
            var originalValue = mappingEntryContainer.attr('original_value');
            var editContainer = $('.popover .edit-mapping-container[original_value="' + originalValue + '"]');
            // editContainer.find('.edit-display-textbox').val(mappingContainer.find('.display-value').text());
            editContainer.find('.cancel-edit-mapping-button').on('click', function () {
                editLink.popover('hide');
            });
        }).on('hidden.bs.popover', function () {
            $(this).removeClass('stay-visible');
        });


        //
        // show/hide mappings link
        //

        $('.show-mappings-link').on('click', function () {
            var mappingContainer = $(this).closest('.mapping-container');
            mappingContainer.find('.mapping-table').toggle();
        });

        //
        // fix for popover bug: https://stackoverflow.com/questions/32581987
        //

        $('body').on('hidden.bs.popover', function (e) {
            $(e.target).data("bs.popover").inState = {click: false, hover: false, focus: false}
        });
    }
});
