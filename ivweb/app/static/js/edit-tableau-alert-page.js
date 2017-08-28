$.widget("custom.edittableaualertpage", {
    options: {
        editExisting: false,
        templateChoicesUrl: '',
        trustedReportUrl: '',
        selectedPublisher: null,
        isSinglePublisherUser: false
    },

    _create: function () {
        var self = this;

        this.filters = {};
        this.parameters = {};
        this.selectedAlertType = null;
        this.hasFilterConfiguration = false;
        this.embeddedReportLoaded = false;
        this.currentAutoAppliedAfterLoadFilters = {};
        this.viz = null;

        this.emailSplitRegex = /[\s,;]+/;
        this.emailTestRegex = /^([a-zA-Z0-9_.+-])+\@(([a-zA-Z0-9-])+\.)+([a-zA-Z0-9]{2,4})+$/;

        this.validAttachmentOnlyEmailsTimeoutId = null;
        this.validFullEmailsTimeoutId = null;

        this.filtersHiddenInput = $('#id_alert_filters');
        this.parametersHiddenInput = $('#id_alert_params');

        $('#id_name, #id_attachment_only_emails, #id_full_emails').on('keyup', function () {
            self._checkForm();
        });

        $('.alert-form').on('submit', function () {
            $('.submit-button').addClass('disabled').prop('disabled', false);
        });

        if (this.options.editExisting) {
            $('.alert-type-controls').show();
            $('.alert-choice-controls').show();
            var selectedAlertType = $('.alert-type-choice-list li.selected');
            self.selectedAlertType = selectedAlertType.attr('alert_type');
            var selectedTemplate = $('.template-choice-list li.selected');
            $('#id_template_id').val(selectedTemplate.attr('template_id'));
            this.hasFilterConfiguration = selectedTemplate.attr('has_filter_configuration') === '1';
            self._updateFilterConfiguration();
            this.filters = JSON.parse($('#id_alert_filters').val());
            this.parameters = JSON.parse($('#id_alert_params').val());
            this._checkForm();
        }
        else {
            $('.alert-type-choice-list li').on('click', function () {
                var selectedItem = $(this);
                selectedItem.addClass('selected').siblings().removeClass('selected');
                self.selectedAlertType = selectedItem.attr('alert_type');
                $('#id_template_id').val('');
                self.embeddedReportLoaded = false;
                self._updateTemplateChoices();
                self._checkForm();
            });

            if (this.options.isSinglePublisherUser) {
                self._updateTemplateChoices();
            }
            else {
                var publisherMenu = $('#id_publisher_id');

                var nullPublisherItem = publisherMenu.find('option:first-child');
                nullPublisherItem.attr('disabled', 'disabled');
                if (this.options.selectedPublisher) {
                    self._updateTemplateChoices();
                }
                else {
                    publisherMenu.addClass('placeholder');
                    nullPublisherItem.attr('selected', 'selected');
                }

                publisherMenu.on('change', function () {
                    var selectedOption = publisherMenu.find('option:selected');
                    if (!selectedOption.attr('disabled')) {
                        publisherMenu.removeClass('placeholder');
                        self._updateTemplateChoices();
                    }
                    self._checkForm();
                });
            }
        }

        var allSteps = $('.wizard-step');
        var chooseAlertButton = $('.choose-alert-button');
        chooseAlertButton.on('click', function (event) {
            if (!chooseAlertButton.hasClass('disabled')) {
                allSteps.hide();
                $('#step-choose-alert').show();
                $('.choose-alert-tab').addClass('active').siblings().removeClass('active');
                self._checkForm();
            }
            event.preventDefault();
        });
        var configureNotificationsButton = $('.configure-notifications-button');
        configureNotificationsButton.on('click', function () {
            if (!configureNotificationsButton.hasClass('disabled')) {
                allSteps.hide();
                $('#step-configure-notifications').show();
                $('.configure-notifications-tab').addClass('active').siblings().removeClass('active');
                self._checkForm();
            }
            event.preventDefault();
        });
        var setFiltersButton = $('.set-filters-button');
        setFiltersButton.on('click', function () {
            if (!setFiltersButton.hasClass('disabled')) {
                allSteps.hide();
                $('#step-set-filters').show();
                $('.set-filters-tab').addClass('active').siblings().removeClass('active');
                if (!self.embeddedReportLoaded) {
                    self._clearEmbeddedReport();
                    if (self.options.editExisting) {
                        self._loadEmbeddedReport(true);
                    }
                    else {
                        self._loadEmbeddedReport(false);
                    }
                }
                self._checkForm();
            }
            event.preventDefault();
        });
        var reviewButton = $('.review-button');
        reviewButton.on('click', function () {
            if (!reviewButton.hasClass('disabled')) {
                allSteps.hide();
                $('#step-review').show();
                $('.review-tab').addClass('active').siblings().removeClass('active');
                self._checkForm();
            }
            event.preventDefault();
        });

        var filterSummaryItem = this.element.find('.filter-summary-item');
        var filterDetails = this.element.find('.filter-details');
        this.element.find('.filter-details-toggle').on('click', function (event) {
            if (filterDetails.is(':visible')) {
                filterDetails.hide();
                filterSummaryItem.removeClass('dropup');
            }
            else {
                filterDetails.show();
                filterSummaryItem.addClass('dropup');
            }
            event.preventDefault();
        })
    },

    _updateTemplateChoices: function () {
        var self = this;

        var alertTypeControls = $('.alert-type-controls');
        var alertChoiceControls = $('.alert-choice-controls');

        var publisherId = this._getSelectedPublisherId();
        if (!publisherId) {
            alertTypeControls.hide();
            alertChoiceControls.hide();
        }
        else {
            // hard coded selection of scheduled alert type
            $('.alert-type-choice-list [alert_type="scheduled"]').addClass('selected');
            this.selectedAlertType = 'scheduled';

            alertTypeControls.show();
            $('.article-type-instructions-' + this.selectedAlertType).show().siblings().hide();

            if (!this.selectedAlertType) {
                alertChoiceControls.hide();
            }
            else {
                var data = {
                    publisher_id: publisherId,
                    alert_type: self.selectedAlertType
                };

                $.get(this.options.templateChoicesUrl, data)
                    .done(function (html) {
                        alertChoiceControls.show();
                        $('.template-choices-control-container').html(html);
                        self._wireTemplateChoiceList();
                    });
            }
        }
    },

    _wireTemplateChoiceList: function () {
        var self = this;

        $('.template-choice-list li').on('click', function () {
            var selectedItem = $(this);
            var selectedTemplateId = selectedItem.attr('template_id');

            if (selectedTemplateId) {
                selectedItem.addClass('selected').siblings().removeClass('selected');

                $('#id_template_id').val(selectedTemplateId);

                self.hasFilterConfiguration = selectedItem.attr('has_filter_configuration') === '1';
                self._updateFilterConfiguration();

                // clear out any existing embedded report
                self.embeddedReportLoaded = false;

                // wire up the alert name
                selectedItem.find('input.threshold-input').on('keyup', function () {
                    self._updateAlertName();
                });
                self._updateAlertName();

                self._checkForm();
            }
        });
    },

    _updateFilterConfiguration: function () {
        if (this.hasFilterConfiguration) {
            $('.filter-configuration').show();
            $('.no-filter-configuration').hide();
        }
        else {
            $('.filter-configuration').hide();
            $('.no-filter-configuration').show();
        }
    },

    _updateAlertName: function () {
        var selectedItem = $('.template-choice-list li.selected');
        var thresholdValue = selectedItem.find('input.threshold-input').val();
        var nameTemplate = selectedItem.attr('name_template');
        var renderedName = nameTemplate.replace('%%', '%').replace('%s', thresholdValue);
        $('#id_name').val(renderedName);
    },

    _clearEmbeddedReport: function () {
        if (this.viz) {
            this.viz.dispose();
        }
        $('.embedded-report-container').empty();
    },

    _loadEmbeddedReport: function (useExistingFilters) {
        var self = this;

        var selectedTemplate = $('#id_template_id').val();
        if (selectedTemplate) {
            IvetlWeb.showLoading();

            data = {
                publisher_id: this._getSelectedPublisherId(),
                template_id: selectedTemplate,
                embed_type: 'configure'
            };

            $.get(this.options.trustedReportUrl, data)
                .done(function (response) {
                    var trustedReportUrl = response.url;
                    var controls = $('.embedded-report-controls');
                    controls.show();
                    var reportContainer = controls.find('.embedded-report-container')[0];

                    var filterWorksheetName = $('.template-choice-list li.selected').attr('filter_worksheet_name');

                    var allExistingFilters = JSON.parse(self.filtersHiddenInput.val());
                    var allExistingParameters = JSON.parse(self.parametersHiddenInput.val());

                    var viz = null;

                    var vizOptions = {
                        width: reportContainer.offsetWidth,
                        height: reportContainer.offsetHeight,
                        hideTabs: false,
                        hideToolbar: true,
                        onFirstInteractive: function () {
                            if (useExistingFilters) {
                                var workbook = viz.getWorkbook();
                                var activeSheet = workbook.getActiveSheet();

                                if (activeSheet.getSheetType() !== 'worksheet') {
                                    var allWorksheets = activeSheet.getWorksheets();
                                    for (var i = 0; i < allWorksheets.length; i++) {
                                        var worksheet = allWorksheets[i];
                                        if (worksheet.getName() === filterWorksheetName) {
                                            activeSheet = worksheet;
                                            break;
                                        }
                                    }
                                }

                                // parameters get applied after load
                                $.each(Object.keys(allExistingParameters), function (index, name) {
                                    var parameter = allExistingParameters[name];
                                    workbook.changeParameterValueAsync(name, parameter.values[0]);
                                });

                                // ranges and excluded value filters get applied after load
                                $.each(Object.keys(allExistingFilters), function (index, name) {
                                    var filter = allExistingFilters[name];

                                    if (filter.type === 'categorical' && filter.exclude) {
                                        self.currentAutoAppliedAfterLoadFilters[name] = true;
                                        activeSheet.applyFilterAsync(name, filter.values, tableauSoftware.FilterUpdateType.REMOVE);
                                    }
                                    else if (filter.type === 'quantitative') {
                                        self.currentAutoAppliedAfterLoadFilters[name] = true;
                                        var minDate = new Date(filter.min);
                                        var maxDate = new Date(filter.max);
                                        activeSheet.applyRangeFilterAsync(name, {min: minDate, max: maxDate})
                                            .otherwise(function (err) {
                                                console.log('Error setting range filter: ' + err);
                                            });
                                    }
                                });
                            }
                        }
                    };

                    // regular categorical filters get applied during load
                    if (useExistingFilters) {
                        $.each(Object.keys(allExistingFilters), function (index, name) {
                            var filter = allExistingFilters[name];
                            if (filter.type === 'categorical' && !filter.exclude) {
                                vizOptions[name] = [];
                                $.each(filter.values, function (index, value) {
                                    vizOptions[name].push(value);
                                });
                            }
                        });
                    }
                    else {
                        // clear out existing filters and parameters
                        self.filters = {};
                        self.parameters = {};
                        self.filtersHiddenInput.val('{}');
                        self.parametersHiddenInput.val('{}');
                    }

                    viz = new tableau.Viz(reportContainer, trustedReportUrl, vizOptions);

                    viz.addEventListener(tableau.TableauEventName.FILTER_CHANGE, function (e) {
                        e.getFilterAsync().then(function (filter) {
                            var filterName = filter.getFieldName();
                            var runConfirmSelectAll = false;
                            var numberOfSelectedValues = 0;
                            var changed = false;
                            var filterType = filter.getFilterType();
                            if (filterType === 'quantitative') {
                                // TODO: ranges are ignored for now, will come back to this
                                // var min = filter.getMin();
                                // var max = filter.getMax();
                                // if (!(filterName in self.filters) || self.filters[filterName].min != min || self.filters[filterName].max != max) {
                                //     changed = true;
                                //     self.filters[filterName] = {
                                //         type: 'quantitative',
                                //         min: new Date(min.value).toISOString(),
                                //         max: new Date(max.value).toISOString()
                                //     };
                                // }
                            }
                            else if (filterType === 'categorical') {
                                var selectedValues = filter.getAppliedValues();

                                // figure out if anything has changed, in an effort to ignore repeated event firing
                                var exclude = filter.getIsExcludeMode();
                                if (filterName in self.filters && self.filters[filterName].exclude === exclude && selectedValues.length === self.filters[filterName].values.length) {
                                    $.each(selectedValues, function (index, value) {
                                        if (self.filters[filterName].values.indexOf(value.value) === -1) {
                                            changed = true;
                                            return false;
                                        }
                                    });
                                }
                                else {
                                    changed = true;
                                }

                                if (changed) {
                                    self.filters[filterName] = {
                                        type: 'categorical',
                                        exclude: exclude,
                                        values: []
                                    };

                                    $.each(selectedValues, function (index, value) {
                                        self.filters[filterName].values.push(value.value);
                                    });
                                    numberOfSelectedValues = selectedValues.length;
                                    if (numberOfSelectedValues > 10 && !self.currentAutoAppliedAfterLoadFilters[filterName]) {
                                        runConfirmSelectAll = true;
                                    }

                                    self.currentAutoAppliedAfterLoadFilters[name] = false;
                                }
                            }

                            if (changed) {
                                self.filtersHiddenInput.val(JSON.stringify(self.filters));
                                self._checkForm();
                            }

                            if (runConfirmSelectAll) {
                                self._confirmSelectAll(filterName, numberOfSelectedValues);
                            }
                        });
                    });

                    viz.addEventListener(tableau.TableauEventName.PARAMETER_VALUE_CHANGE, function (e) {

                        e.getParameterAsync().then(function (parameter) {
                            var parameterName = parameter.getName();
                            self.parameters[parameterName] = {
                                type: 'categorical',
                                exclude: false,
                                values: [parameter.getCurrentValue().formattedValue]
                            };

                            self.parametersHiddenInput.val(JSON.stringify(self.parameters));
                            self._checkForm();
                        });
                    });

                    self.embeddedReportLoaded = true;
                    self.viz = viz;
                })
                .always(function () {
                    IvetlWeb.hideLoading();
                });
        }
        else {
            controls.hide();
        }
    },

    _confirmSelectAll: function (filterName, numberOfSelectedValues) {
        var self = this;
        var m = $('#confirm-select-all-modal');

        m.find('.filter-name').html(filterName);
        m.find('.number-of-values').html(numberOfSelectedValues);

        var allValuesButton = m.find('.use-all-values-button');
        var specificValuesButton = m.find('.use-specific-values-button');

        var closeModal = function () {
            allValuesButton.off('click');
            specificValuesButton.off('click');
            m.off('hidden.bs.modal');
            m.modal('hide');
        };

        allValuesButton.on('click', function () {

            // delete the value from filters
            delete self.filters[filterName];
            self.filtersHiddenInput.val(JSON.stringify(self.filters));

            // reload the viz without that filter
            self._clearEmbeddedReport();
            self._loadEmbeddedReport(true);

            closeModal();
        });

        specificValuesButton.on('click', function () {
            // leave filters as-is
            closeModal();
        });

        m.modal();
    },

    _getSelectedPublisherId: function () {
        if (this.options.editExisting || this.options.isSinglePublisherUser) {
            return $('#id_publisher_id').val();
        }
        else {
            return $("#id_publisher_id option:selected").val();
        }
    },

    _getSelectedPublisherName: function () {
        if (this.options.editExisting || this.options.isSinglePublisherUser) {
            return $('#id_publisher_name').val();
        }
        else {
            return $("#id_publisher_id option:selected").text();
        }
    },

    _checkForm: function () {
        var self = this;

        var publisherId = this._getSelectedPublisherId();
        var templateId = $("#id_template_id").val();

        if (publisherId && templateId) {
            $('.configure-notifications-button').removeClass('disabled').prop('disabled', false);
            $('.publisher-summary-item').html(this._getSelectedPublisherName());
            $('.alert-summary-item').html($('.template-choice-list .selected').text().trim());
        }
        else {
            $('.configure-notifications-button').addClass('disabled').prop('disabled', false);
        }

        var name = $('#id_name').val();

        var attachmentOnlyEmails = $('#id_attachment_only_emails').val();
        var validAttachmentOnlyEmails = true;
        var atLeastOneAttachmentOnlyEmail = false;
        if (attachmentOnlyEmails) {
            $.each(attachmentOnlyEmails.split(self.emailSplitRegex), function (index, email) {
                email = email.trim();
                if (email) {
                    if (self.emailTestRegex.test(email)) {
                        atLeastOneAttachmentOnlyEmail = true;
                    }
                    else {
                        validAttachmentOnlyEmails = false;
                    }
                }
            });
        }

        clearTimeout(self.validAttachmentOnlyEmailsTimeoutId);
        if (validAttachmentOnlyEmails) {
            $('.attachment-only-emails-error-message').hide();
        }
        else {
            self.validAttachmentOnlyEmailsTimeoutId = setTimeout(function () {
                $('.attachment-only-emails-error-message').show();
            }, 1000);
        }

        var fullEmails = $('#id_full_emails').val();
        var validFullEmails = true;
        var atLeastOneFullEmail = false;
        if (fullEmails) {
            $.each(fullEmails.split(self.emailSplitRegex), function (index, email) {
                email = email.trim();
                if (email) {
                    if (self.emailTestRegex.test(email)) {
                        atLeastOneFullEmail = true;
                    }
                    else {
                        validFullEmails = false;
                    }
                }
            });
        }

        clearTimeout(self.validFullEmailsTimeoutId);
        if (validFullEmails) {
            $('.full-emails-error-message').hide();
        }
        else {
            self.validFullEmailsTimeoutId = setTimeout(function () {
                $('.full-emails-error-message').show();
            }, 1000);
        }

        if (name && (atLeastOneAttachmentOnlyEmail || atLeastOneFullEmail) && validAttachmentOnlyEmails && validFullEmails) {
            $('.set-filters-button').removeClass('disabled').prop('disabled', false);
            $('.name-summary-item').html(name);
            if (attachmentOnlyEmails) {
                $('.attachment-only-emails-summary-item').html(attachmentOnlyEmails);
            }
            else {
                $('.attachment-only-emails-summary-item').html('None');
            }
            if (fullEmails) {
                $('.full-emails-summary-item').html(fullEmails);
            }
            else {
                $('.full-emails-summary-item').html('None');
            }
            $('.review-button').removeClass('disabled').prop('disabled', false);
            $('.submit-button').removeClass('disabled').prop('disabled', false);
        }
        else {
            $('.set-filters-button').addClass('disabled').prop('disabled', false);
            $('.review-button').addClass('disabled').prop('disabled', false);
            $('.submit-button').addClass('disabled').prop('disabled', false);
        }

        var filtersString = $('#id_alert_filters').val();
        var parametersString = $('#id_alert_params').val();

        var filterSummary = $('.filter-summary-item');
        var hasFilters = filterSummary.find('.has-filters');
        var noFilters = filterSummary.find('.no-filters');
        if ((filtersString && filtersString != '{}') || (parametersString && parametersString != '{}')) {
            var allFilters = JSON.parse(filtersString);
            $.extend(allFilters, JSON.parse(parametersString));

            var filterHtml = '';
            for (var filterName in allFilters) {
                var filter = allFilters[filterName];
                if (filter.type == 'categorical') {
                    var filterValues = filter.values;
                    var filterValuesString = '';
                    if ($.isArray(filterValues)) {
                        filterValuesString = filterValues.join(', ');
                    }
                    else {
                        filterValuesString = filterValues.toString();
                    }

                    var excludeString = '';
                    if (filter.exclude) {
                        excludeString = ' (excluded)';
                    }

                    filterHtml += '<p>' + filterName + excludeString + ' = ' + filterValuesString + '</p>';
                }
                else if (filter.type == 'quantitative') {
                    var r = /.*\((.*)\)/;
                    var matches = r.exec(filterName);
                    if (matches && matches.length == 2) {
                        filterName = matches[1];
                    }

                    var minLabel = moment(new Date(filter.min)).utc().format('M/D/YYYY');
                    var maxLabel = moment(new Date(filter.max)).utc().format('M/D/YYYY');
                    filterHtml += '<p>' + filterName + ' = ' + minLabel + ' to ' + maxLabel + '</p>';
                }
            }
            filterSummary.find('.filter-details').html(filterHtml);

            var filterToggleLabel = '';
            var numFilters = Object.keys(allFilters).length;
            if (numFilters > 1) {
                filterToggleLabel = numFilters + ' filters';
            }
            else {
                filterToggleLabel = '1 filter';
            }
            filterSummary.find('.filter-details-toggle').text(filterToggleLabel);

            noFilters.hide();
            hasFilters.show();
        }
        else {
            noFilters.show();
            hasFilters.hide();
        }
    }
});
