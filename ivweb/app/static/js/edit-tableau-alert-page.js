$.widget("custom.edittableaualertpage", {
    options: {
        reportChoicesUrl: '',
        trustedReportUrl: '',
        selectedPublisher: null,
        selectedReport: null,
        isSinglePublisherUser: false
    },

    _create: function() {
        var self = this;

        this.filters = {};
        this.selectedAlertType = null;
        this.embeddedReportLoaded = false;

        $('#id_name, #id_attachment_only_emails, #id_full_emails').on('keyup', function() {
            self._checkForm();
        });

        $('.alert-type-choice-list li').on('click', function () {
            var selectedItem = $(this);
            selectedItem.addClass('selected').siblings().removeClass('selected');
            self.selectedAlertType = selectedItem.attr('alert_type');
            $('#id_report_id').val('');
            self.embeddedReportLoaded = false;
            self._updateReportChoices();
            self._checkForm();
        });

        if (this.options.isSinglePublisherUser) {
            self._updateReportChoices();
        }
        else {
            var publisherMenu = $('#id_publisher_id');

            var nullPublisherItem = publisherMenu.find('option:first-child');
            nullPublisherItem.attr('disabled', 'disabled');
            if (!this.options.selectedPublisher) {
                publisherMenu.addClass('placeholder');
                nullPublisherItem.attr('selected', 'selected');
            }

            publisherMenu.on('change', function () {
                var selectedOption = publisherMenu.find('option:selected');
                if (!selectedOption.attr('disabled')) {
                    publisherMenu.removeClass('placeholder');
                    self._updateReportChoices();
                }
                self._checkForm();
            });
        }

        var allSteps = $('.wizard-step');
        var chooseAlertButton = $('.choose-alert-button');
        chooseAlertButton.on('click', function(event) {
            if (!chooseAlertButton.hasClass('disabled')) {
                allSteps.hide();
                $('#step-choose-alert').show();
                $('.choose-alert-tab').addClass('active').siblings().removeClass('active');
                self._checkForm();
            }
            event.preventDefault();
        });
        var configureNotificationsButton = $('.configure-notifications-button');
        configureNotificationsButton.on('click', function() {
            if (!configureNotificationsButton.hasClass('disabled')) {
                allSteps.hide();
                $('#step-configure-notifications').show();
                $('.configure-notifications-tab').addClass('active').siblings().removeClass('active');
                self._checkForm();
            }
            event.preventDefault();
        });
        var setFiltersButton = $('.set-filters-button');
        setFiltersButton.on('click', function() {
            if (!setFiltersButton.hasClass('disabled')) {
                allSteps.hide();
                $('#step-set-filters').show();
                $('.set-filters-tab').addClass('active').siblings().removeClass('active');
                if (!self.embeddedReportLoaded) {
                    self._loadEmbeddedReport();
                }
                self._checkForm();
            }
            event.preventDefault();
        });
        var reviewButton = $('.review-button');
        reviewButton.on('click', function() {
            if (!reviewButton.hasClass('disabled')) {
                allSteps.hide();
                $('#step-review').show();
                $('.review-tab').addClass('active').siblings().removeClass('active');
                self._checkForm();
            }
            event.preventDefault();
        });
    },

    _updateReportChoices: function() {
        var self = this;

        var alertTypeControls = $('.alert-type-controls');
        var alertChoiceControls = $('.alert-choice-controls');

        if (!$('#id_publisher_id option:selected').val()) {
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
                    publisher_id: $('#id_publisher_id option:selected').val(),
                    alert_type: self.selectedAlertType
                };

                $.get(this.options.reportChoicesUrl, data)
                    .done(function(html) {
                        alertChoiceControls.show();
                        $('.report-choices-control-container').html(html);

                        $('.report-choice-list li').on('click', function() {
                            var selectedItem = $(this);
                            var selectedReportId = selectedItem.attr('report_id');

                            if (selectedReportId) {
                                selectedItem.addClass('selected').siblings().removeClass('selected');

                                $('#id_report_id').val(selectedReportId);

                                // clear out any existing embedded report
                                self.embeddedReportLoaded = false;

                                // wire up the alert name
                                selectedItem.find('input.threshold-input').on('keyup', function() {
                                    self._updateAlertName();
                                });
                                self._updateAlertName();

                                self._checkForm();
                            }
                        });
                    });
            }
        }
    },

    _updateAlertName: function() {
        var selectedItem = $('.report-choice-list li.selected');
        var thresholdValue = selectedItem.find('input.threshold-input').val();
        var nameTemplate = selectedItem.attr('name_template');
        var renderedName = nameTemplate.replace('%%', '%').replace('%s', thresholdValue);
        $('#id_name').val(renderedName);
    },

    _loadEmbeddedReport: function() {
        var self = this;

        // clear out existing filter selections
        this.filters = {};

        var selectedReport = $('#id_report_id').find('option:selected').val();
        if (selectedReport != '') {
            IvetlWeb.showLoading();

            $.get(this.options.trustedReportUrl, {report: selectedReport, embed_type: 'configure'})
                .done(function (response) {
                    var trustedReportUrl = response.url;
                    console.log('trusted URL: ' + trustedReportUrl);
                    var controls = $('.embedded-report-controls');
                    controls.show();
                    var reportContainer = controls.find('.embedded-report-container')[0];
                    var viz = new tableau.Viz(reportContainer, trustedReportUrl, {
                        width: reportContainer.offsetWidth,
                        height: reportContainer.offsetHeight,
                        hideTabs: false,
                        hideToolbar: true
                    });

                    viz.addEventListener(tableau.TableauEventName.FILTER_CHANGE, function(e) {
                        e.getFilterAsync().then(function(filter) {
                            self.filters[filter._caption] = [];
                            var selectedValues = filter.getAppliedValues();
                            $.each(selectedValues, function(index, value) {
                                self.filters[filter._caption].push(value.value);
                            });
                            $('#id_alert_filters').val(JSON.stringify(self.filters));
                            self._checkForm();
                        });
                    });

                    self.embeddedReportLoaded = true;
                })
                .always(function () {
                    IvetlWeb.hideLoading();
                });
        }
        else {
            controls.hide();
        }
    },

    _checkForm: function() {
        var publisherId = $("#id_publisher_id option:selected").val();
        var reportId = $("#id_report_id").val();

        if (publisherId && reportId) {
            $('.configure-notifications-button').removeClass('disabled').prop('disabled', false);
            $('.publisher-summary-item').html('New alert for: ' + publisherId);
            $('.alert-summary-item').html('Alert type: ' + reportId);
            // $('.set-filters-button').removeClass('disabled').prop('disabled', false);
        }
        else {
            $('.configure-notifications-button').addClass('disabled').prop('disabled', false);
        }

        var name = $('#id_name').val();
        var attachmentOnlyEmails = $('#id_attachment_only_emails').val();
        var fullEmails = $('#id_full_emails').val();

        if (name && (attachmentOnlyEmails || fullEmails)) {
            $('.set-filters-button').removeClass('disabled').prop('disabled', false);
            $('.name-summary-item').html('A new alert called: ' + name);
            if (attachmentOnlyEmails) {
                $('.attachment-only-emails-summary-item').html('Attachment-only emails for: ' + attachmentOnlyEmails);
            }
            else {
                $('.attachment-only-emails-summary-item').html('No attachment-only emails will be sent');
            }
            if (fullEmails) {
                $('.full-emails-summary-item').html('Full emails for: ' + fullEmails);
            }
            else {
                $('.full-emails-summary-item').html('No full emails will be sent');
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
            $('.filter-summary-item').html('Apply filters: ' + filters);
        }
        else {
            $('.filter-summary-item').html('No filters');
        }
    }
});
