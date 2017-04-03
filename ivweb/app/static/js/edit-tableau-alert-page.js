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

        if (this.options.editExisting) {
            $('.alert-type-controls').show();
            $('.alert-choice-controls').show();
            var selectedAlertType = $('.alert-type-choice-list li.selected');
            self.selectedAlertType = selectedAlertType.attr('alert_type');
            var selectedTemplate = $('.template-choice-list li.selected');
            $('#id_template_id').val(selectedTemplate.attr('template_id'));
            this.hasFilterConfiguration = selectedTemplate.attr('has_filter_configuration') == '1';
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

                self.hasFilterConfiguration = selectedItem.attr('has_filter_configuration') == '1';
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

                    var vizOptions = {
                        width: reportContainer.offsetWidth,
                        height: reportContainer.offsetHeight,
                        hideTabs: false,
                        hideToolbar: true
                    };

                    if (useExistingFilters) {

                        // apply each of the filters
                        var existingFilters = JSON.parse(self.filtersHiddenInput.val());
                        $.each(Object.keys(existingFilters), function (index, name) {
                            vizOptions[name] = [];
                            $.each(existingFilters[name], function (index, value) {
                                vizOptions[name].push(value);
                                console.log('apply filter: ' + name + ' = ' + value);
                            });
                        });

                        // apply each of the params
                        var existingParams = JSON.parse(self.parametersHiddenInput.val());
                        $.each(Object.keys(existingParams), function (index, name) {
                            vizOptions[name] = [];
                            $.each(existingParams[name], function (index, value) {
                                vizOptions[name].push(value);
                                console.log('apply parameter: ' + name + ' = ' + value);
                            });
                        });
                    }
                    else {
                        // clear out existing filters and parameters
                        self.filters = {};
                        self.parameters = {};
                        self.filtersHiddenInput.val('{}');
                        self.parametersHiddenInput.val('{}');
                    }

                    var viz = new tableau.Viz(reportContainer, trustedReportUrl, vizOptions);

                    viz.addEventListener(tableau.TableauEventName.FILTER_CHANGE, function (e) {
                        e.getFilterAsync().then(function (filter) {
                            var filterName = filter._caption;
                            var selectedValues = filter.getAppliedValues();

                            // figure out if anything has changed, in an effort to ignore repeated event firing
                            var changed = false;
                            if (filterName in self.filters && selectedValues.length == self.filters[filterName].length) {
                                $.each(selectedValues, function (index, value) {
                                    if (self.filters[filterName].indexOf(value.value) == -1) {
                                        changed = true;
                                        return false;
                                    }
                                });
                            }
                            else {
                                changed = true;
                            }

                            if (changed) {
                                self.filters[filterName] = [];
                                $.each(selectedValues, function (index, value) {
                                    console.log(value);
                                    self.filters[filterName].push(value.value);
                                });
                                self.filtersHiddenInput.val(JSON.stringify(self.filters));
                                self._checkForm();
                                var numberOfSelectedValues = selectedValues.length;
                                if (numberOfSelectedValues > 10) {
                                    self._confirmSelectAll(filterName, numberOfSelectedValues)
                                }
                            }
                        });
                    });

                    viz.addEventListener(tableau.TableauEventName.PARAMETER_VALUE_CHANGE, function (e) {
                        e.getParameterAsync().then(function (parameter) {
                            var parameterName = parameter.getName();
                            self.parameters[parameterName] = parameter.getCurrentValue().value;
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

    _checkForm: function () {
        var self = this;

        var publisherId = this._getSelectedPublisherId();
        var templateId = $("#id_template_id").val();

        if (publisherId && templateId) {
            $('.configure-notifications-button').removeClass('disabled').prop('disabled', false);
            $('.publisher-summary-item').html(publisherId);
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

        var filters = $('#id_alert_filters').val();
        if (filters) {
            $('.filter-summary-item').html(filters);
        }
        else {
            $('.filter-summary-item').html('No filters');
        }

        var parameters = $('#id_alert_params').val();
        if (parameters) {
            $('.parameter-summary-item').html(parameters);
        }
        else {
            $('.parameter-summary-item').html('No parameters');
        }
    }
});
