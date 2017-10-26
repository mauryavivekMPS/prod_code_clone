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
        // wire up edit display popovers
        //

        $('.edit-display-value-link').each(function (index, element) {
            var link = $(element);
            self._wireEditDisplayValuePopover(link);
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
        // wire up edit mapping popovers
        //

        $('.edit-mapping-link').each(function (index, element) {
            var link = $(element);
            self._wireEditMappingPopover(link);
        });

        page.on('click', '.popover .edit-mapping-button', function (event) {
            var editContainer = $(event.target).closest('.edit-mapping-container');
            var originalValue = editContainer.attr('original_value');
            var textbox = editContainer.find('.edit-mapping-textbox');
            var typedValue = textbox.val();
            var selectedMappingValue = textbox.typeahead('getActive');
            var mappingEntryContainer = $('.mapping-entry-container[original_value="' + originalValue + '"]');
            var oldCanonicalValue = mappingEntryContainer.closest('.mapping-container').attr('canonical_value');

            var isNewValue = false;
            var newValue = '';
            var newDisplayValue = '';
            if (selectedMappingValue.name === typedValue) {
                newValue = selectedMappingValue.id;
                newDisplayValue = selectedMappingValue.name;
            }
            else {
                isNewValue = true;
                newValue = typedValue;
                newDisplayValue = typedValue;
            }

            var destinationMappingContainer = page.find('.mapping-container[canonical_value="' + newValue + '"]');

            IvetlWeb.showLoading();

            var data = {
                'publisher_id': self.options.publisherId,
                'mapping_type': self.options.mappingType,
                'original_value': originalValue,
                'canonical_value': newValue,
                'is_new_value': isNewValue ? '1' : '0',
                'csrfmiddlewaretoken': self.options.csrfToken
            };

            $.post('/updatevaluemapping/', data)
                .done(function (response) {
                    mappingEntryContainer.find('.edit-mapping-link').popover('hide');
                    var numRowsBeforeDetach = mappingEntryContainer.closest('.mapping-table').find('.mapping-entry-container').length;
                    var numRowsRemaining = numRowsBeforeDetach - 1;
                    var originalMappingContainer = mappingEntryContainer.closest('.mapping-container');

                    mappingEntryContainer.before(
                        '<tr class="ghost-row" original_value="' + originalValue + '">' +
                            '<td>' + originalValue + '<span class="lnr lnr-arrow-right moved-to-message-arrow"></span>' +
                            '<span class="moved-to-message">Moved to ' + newDisplayValue + '</span></td>' +
                        '</tr>'
                    );
                    mappingEntryContainer.detach();

                    if (isNewValue) {
                        var containerBefore = null;
                        var lowerCaseNewValue = newValue.toLowerCase();
                        $('.mapping-container').each(function (index, element) {
                            var c = $(element);
                            if (c.find('.display-value').text().toLowerCase() < lowerCaseNewValue) {
                                containerBefore = c;
                            }
                        });

                        if (containerBefore) {
                            console.log('found containerBefore');
                            console.log(containerBefore);
                            containerBefore.after(response.new_mapping_html);
                        }
                        else {
                            console.log('no containerBefore, prepending to allMappingContainers');
                            $('.all-mapping-containers').prepend(response.new_mapping_html);
                        }

                        destinationMappingContainer = $('.mapping-container[canonical_value="' + newValue + '"]');
                        destinationMappingContainer.find('.edit-display-value-link').each(function (index, element) {
                            var link = $(element);
                            self._wireEditDisplayValuePopover(link);
                        });
                        destinationMappingContainer.find('.edit-mapping-link').each(function (index, element) {
                            var link = $(element);
                            self._wireEditMappingPopover(link);
                        });

                        var insertedNewChoice = false;
                        var newChoice = {id: newValue, name: newValue};
                        $.each(self.allCanonicalChoices, function (index, choice) {
                            if (choice.name.toLowerCase() > lowerCaseNewValue) {
                                self.allCanonicalChoices.splice(index, 0, newChoice);
                                insertedNewChoice = true;
                                return false;
                            }
                        });
                        if (!insertedNewChoice) {
                            self.allCanonicalChoices.push(newChoice);
                        }
                    }
                    else {
                        var destinationTable = destinationMappingContainer.find('.mapping-table tbody');
                        destinationTable.append(mappingEntryContainer);
                    }

                    destinationMappingContainer.addClass('finished-move-target');
                    self._updateValueCounts();

                    setTimeout(function () {
                        var ghostRow = $('.ghost-row[original_value="' + originalValue + '"]');
                        ghostRow.fadeOut(500, function () {
                            ghostRow.remove();
                            destinationMappingContainer.removeClass('finished-move-target');

                            // if no rows left, remove the whole category
                            if (numRowsRemaining < 1) {
                                $.each(self.allCanonicalChoices, function (index, choice) {
                                    if (choice.id === oldCanonicalValue) {
                                        self.allCanonicalChoices.splice(index, 1);
                                        return false;
                                    }
                                });
                                originalMappingContainer.remove();
                            }
                        });
                    }, 1500);

                    IvetlWeb.hideLoading();
                });

            console.log('preventing 2');
            event.preventDefault();
        });

        page.on('keyup change', '.popover .edit-mapping-textbox', function (event) {
            self._removeAllMoveTargets();
            var textbox = $(this);
            var currentValue = textbox.val();
            var editContainer = $(event.target).closest('.edit-mapping-container');
            var button = editContainer.find('.edit-mapping-button');
            if (currentValue === '') {
                button.addClass('disabled').attr('disabled', true);
            }
            else {
                button.removeClass('disabled').attr('disabled', false);
                var selectedMappingValue = textbox.typeahead('getActive');
                if (selectedMappingValue && selectedMappingValue.name === textbox.val()) {
                    button.text('Move');
                    self._setMoveTarget(selectedMappingValue.id);
                }
                else {
                    button.text('Create');
                }
            }
        });


        //
        // show/hide mappings link
        //

        page.on('click', '.display-value-opener-link', function (event) {
            var mappingContainer = $(this).closest('.mapping-container');
            if (mappingContainer.find('.mapping-table').is(':visible')) {
                self._hideMappings(mappingContainer);
            }
            else {
                self._showMappings(mappingContainer);
            }

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
        // fix for two-click popover bug: https://stackoverflow.com/questions/32581987
        //

        $('body').on('hidden.bs.popover', function (e) {
            $(e.target).data("bs.popover").inState = {click: false, hover: false, focus: false}
        });

        //
        // fix for dismiss on outside click: https://stackoverflow.com/questions/11703093
        //

        $(document).on('click', function (e) {
            $('[data-toggle="popover"],[data-original-title]').each(function () {
                //the 'is' for buttons that trigger popups
                //the 'has' for icons within a button that triggers a popup
                if (!$(this).is(e.target) && $(this).has(e.target).length === 0 && $('.popover').has(e.target).length === 0) {
                    (($(this).popover('hide').data('bs.popover') || {}).inState || {}).click = false  // fix for BS 3.3.6
                }

            });
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
                    var spinner = $('.update-reports-spinner');
                    spinner.show();
                    setTimeout(function () {
                        spinner.hide();
                        $('.running-pipeline-message').show();
                    }, 1000);
                    IvetlWeb.hideLoading();
                });

            event.preventDefault();
        });
    },

    _wireEditDisplayValuePopover: function (link) {
        link.popover({
            html: true,
            title: 'Enter a new display value',
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
    },

    _wireEditMappingPopover: function (link) {
        var self = this;
        link.popover({
            html: true,
            title: 'Choose a new mapping',
            placement: 'auto right',
            content: function () {
                return $(this).closest('.mapping-entry-container').find('.edit-mapping-popover').html();
            }
        }).on('click', function (event) {
            event.preventDefault();
        }).on('inserted.bs.popover', function () {
            var editLink = $(this);
            editLink.addClass('stay-visible');
            var mappingEntryContainer = editLink.closest('.mapping-entry-container');
            var originalValue = mappingEntryContainer.attr('original_value');
            var editContainer = $('.popover .edit-mapping-container[original_value="' + originalValue + '"]');

            var canonicalValue = mappingEntryContainer.closest('.mapping-container').attr('canonical_value');
            var filteredCanonicalChoices = [];
            $.each(self.allCanonicalChoices, function (index, choice) {
                if (choice.id !== canonicalValue){
                    filteredCanonicalChoices.push(choice);
                }
            });

            var editTextbox = editContainer.find('.edit-mapping-textbox');
            editTextbox.typeahead({
                source: filteredCanonicalChoices
            });
            editTextbox.focus();

            editContainer.find('.cancel-edit-mapping-button').on('click', function (event) {
                editLink.popover('hide');
                event.preventDefault();
            });
        }).on('hidden.bs.popover', function () {
            $(this).removeClass('stay-visible');
            self._removeAllMoveTargets();

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
    },

    _setMoveTarget: function (canonicalValue) {
        $('.mapping-container[canonical_value="' + canonicalValue + '"]').addClass('move-target');
    },

    _removeAllMoveTargets: function () {
        $('.mapping-container').removeClass('move-target');
    }
});
