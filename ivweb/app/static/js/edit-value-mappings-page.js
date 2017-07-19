$.widget("custom.editvaluemappingspage", {
    options: {
        publisherId: '',
        mappingType: '',
        initialCanonicalChoices: [],
        csrfToken: ''
    },

    _create: function () {
        var self = this;

        self.allCanonicalChoices = this.options.initialCanonicalChoices;
        var page = $('#edit-value-mappings-page');

        self._updateValueCounts();

        //
        // wire up edit display popover
        //

        $('.edit-display-value-link').popover({
            html: true,
            title: 'Enter a new display value',
            container: '#edit-value-mappings-page',
            placement: 'auto right',
            content: function () {
                return $(this).closest('.mapping-container').find('.edit-display-popover').html();
            }
        }).on('click', function (event) {
            event.preventDefault();
        }).on('inserted.bs.popover', function () {
            var editLink = $(this);
            editLink.addClass('stay-visible');
            var mappingContainer = $(this).closest('.mapping-container');
            var canonicalValue = $(this).closest('.mapping-container').attr('canonical_value');
            var editContainer = $('.popover .edit-display-container[canonical_value="' + canonicalValue + '"]');
            editContainer.find('.edit-display-textbox').val(mappingContainer.find('.display-value').text());
            editContainer.find('.cancel-edit-display-button').on('click', function (event) {
                editLink.popover('hide');
                event.preventDefault();
            });
        }).on('hidden.bs.popover', function () {
            $(this).removeClass('stay-visible');
        });

        page.on('click', '.popover .edit-display-button', function (event) {
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

            event.preventDefault();
        });

        //
        // wire up edit mapping popover
        //

        $('.edit-mapping-link').popover({
            html: true,
            title: 'Choose a new mapping',
            container: '#edit-value-mappings-page',
            placement: 'auto right',
            content: function () {
                return $(this).closest('.mapping-entry-container').find('.edit-mapping-popover').html();
            }
        }).on('click', function (event) {
            event.preventDefault();
        }).on('inserted.bs.popover', function () {
            var editLink = $(this);
            editLink.addClass('stay-visible');
            var mappingEntryContainer = $(this).closest('.mapping-entry-container');
            var originalValue = mappingEntryContainer.attr('original_value');
            var editContainer = $('.popover .edit-mapping-container[original_value="' + originalValue + '"]');

            var editTextbox = editContainer.find('.edit-mapping-textbox');
            editTextbox.typeahead({
                source: self.allCanonicalChoices,
                showHintOnFocus: true,
                autoSelect: true
            });

            editContainer.find('.cancel-edit-mapping-button').on('click', function (event) {
                editLink.popover('hide');
                event.preventDefault();
            });
        }).on('hidden.bs.popover', function () {
            $(this).removeClass('stay-visible');
        });

        page.on('click', '.popover .edit-mapping-button', function (event) {
            var editContainer = $(event.target).closest('.edit-mapping-container');
            var originalValue = editContainer.attr('original_value');
            var textbox = editContainer.find('.edit-mapping-textbox');
            var newMappingValue = textbox.typeahead('getActive').id;

            IvetlWeb.showLoading();

            var data = {
                'publisher_id': self.options.publisherId,
                'mapping_type': self.options.mappingType,
                'original_value': originalValue,
                'canonical_value': newMappingValue,
                'csrfmiddlewaretoken': self.options.csrfToken
            };

            var mappingEntryContainer = $('.mapping-entry-container[original_value="' + originalValue + '"]');

            $.post('/updatevaluemapping/', data)
                .done(function () {
                    mappingEntryContainer.find('.edit-mapping-link').popover('hide');
                    var numRowsBeforeDetach = mappingEntryContainer.closest('.mapping-table').find('.mapping-entry-container').length;
                    var numRowsRemaining = numRowsBeforeDetach - 1;
                    var originalMappingContainer = mappingEntryContainer.closest('.mapping-container');
                    mappingEntryContainer.detach();
                    var destinationTable = page.find('.mapping-container[canonical_value="' + newMappingValue + '"] .mapping-table tbody');
                    destinationTable.append(mappingEntryContainer);

                    // if no rows left, remove the whole category
                    if (numRowsRemaining < 1) {
                        originalMappingContainer.remove();
                    }

                    self._updateValueCounts();
                    IvetlWeb.hideLoading();
                });

            event.preventDefault();
        });

        page.on('keyup change', '.popover .edit-mapping-textbox', function (event) {
            var textbox = $(this);
            var currentValue = textbox.val();
            var editContainer = $(event.target).closest('.edit-mapping-container');
            var button = editContainer.find('.edit-mapping-button');
            if (currentValue === '') {
                button.addClass('disabled').attr('disabled', true);
            }
            else {
                button.removeClass('disabled').attr('disabled', false);
            }
        });


        //
        // show/hide mappings link
        //

        $('.display-value-opener-link').on('click', function (event) {
            var mappingContainer = $(this).closest('.mapping-container');
            if (mappingContainer.find('.mapping-table').is(':visible')) {
                self._hideMappings(mappingContainer);
            }
            else {
                self._showMappings(mappingContainer);
            }

            event.preventDefault();
        });

        $('.show-mappings-link').on('click', function (event) {
            var link = $(this);
            var mappingContainer = link.closest('.mapping-container');
            self._showMappings(mappingContainer);
            event.preventDefault();
        });

        $('.hide-mappings-link').on('click', function (event) {
            var link = $(this);
            var mappingContainer = link.closest('.mapping-container');
            self._hideMappings(mappingContainer);
            event.preventDefault();
        });

        //
        // show/hide all mappings link
        //

        $('.show-all-mappings-link').on('click', function (event) {
            $('.mapping-table').show();
            $('.mapping-header .opener-icon').hide();
            $('.mapping-header .closer-icon').show();
            event.preventDefault();
        });

        $('.hide-all-mappings-link').on('click', function (event) {
            $('.mapping-table').hide();
            $('.mapping-header .closer-icon').hide();
            $('.mapping-header .opener-icon').show();
            event.preventDefault();
        });

        //
        // fix for popover bug: https://stackoverflow.com/questions/32581987
        //

        $('body').on('hidden.bs.popover', function (e) {
            $(e.target).data("bs.popover").inState = {click: false, hover: false, focus: false}
        });

        //
        // run the pipeline
        //

        $('.update-reports-button').on('click', function (event) {
            var button = $(this);
            button.addClass('disabled').attr('disabled', true);
            var data = {
                'publisher_id': self.options.publisherId,
                'csrfmiddlewaretoken': self.options.csrfToken
            };

            IvetlWeb.showLoading();
            $.post('/runrefreshvaluemappings/', data)
                .done(function () {
                    button.hide();
                    $('.running-pipeline-message').show();
                    IvetlWeb.hideLoading();
                });

            event.preventDefault();
        });
    },

    _showMappings: function (mappingContainer) {
        var mappingTable = mappingContainer.find('.mapping-table');
        mappingTable.show();
        mappingContainer.find('.opener-icon').hide();
        mappingContainer.find('.closer-icon').show();
    },

    _hideMappings: function (mappingContainer) {
        var mappingTable = mappingContainer.find('.mapping-table');
        mappingTable.hide();
        mappingContainer.find('.closer-icon').hide();
        mappingContainer.find('.opener-icon').show();
    },

    _updateValueCounts: function () {
        $('.mapping-container').each(function (index, element) {
            var container = $(element);
            var numValues = container.find('.mapping-entry-container').length;
            container.find('.value-count').text(numValues);
        })
    }
});
