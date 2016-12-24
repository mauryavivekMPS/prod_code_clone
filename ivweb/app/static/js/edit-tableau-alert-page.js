$.widget("custom.edittableaualertpage", {
    options: {
        reportChoicesUrl: '',
        trustedReportUrl: '',
        selectedPublisher: null,
        selectedReport: null,
        isSinglePublisherUser: false,
    },

    _create: function() {
        var self = this;

        this.filters = {};
        this.selectedAlertType = null;
        this.embeddedReportLoaded = false;

        $('#id_name, #id_comma_separated_emails').on('keyup', function() {
            self._checkConfigureNotificationsForm();
            self._updateSummary();
        });

        $('.alert-type-choice-list li').on('click', function () {
            var selectedItem = $(this);
            selectedItem.addClass('selected').siblings().removeClass('selected');
            self.selectedAlertType = selectedItem.attr('alert_type');
            $('#id_report_id').val('');
            self.embeddedReportLoaded = false;
            self._updateReportChoices();
            self._checkChooseAlertForm();
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
                self._checkChooseAlertForm();
            });
        }

        var allSteps = $('.wizard-step');
        $('.choose-alert-button').on('click', function() {
            allSteps.hide();
            $('#step-choose-alert').show();
            $('.choose-alert-tab').addClass('active').siblings().removeClass('active');
            self._checkChooseAlertForm();
        });
        $('.configure-notifications-button').on('click', function() {
            allSteps.hide();
            $('#step-configure-notifications').show();
            $('.configure-notifications-tab').addClass('active').siblings().removeClass('active');
            self._checkConfigureNotificationsForm();
        });
        $('.set-filters-button').on('click', function() {
            allSteps.hide();
            $('#step-set-filters').show();
            $('.set-filters-tab').addClass('active').siblings().removeClass('active');
            if (!self.embeddedReportLoaded) {
                self._loadEmbeddedReport();
            }
            self._checkSetFiltersForm();
        });
        $('.review-button').on('click', function() {
            allSteps.hide();
            $('#step-review').show();
            $('.review-tab').addClass('active').siblings().removeClass('active');
            self._checkReviewForm();
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

                                self._checkChooseAlertForm();
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
        this._updateSummary();
    },

    _updateSummary: function() {
        $('.alert-summary .name').html($('#id_name').val());
    },

    _loadEmbeddedReport: function() {
        var self = this;

        console.log('loading report');

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

            $('.set-filters-button').removeClass('disabled').prop('disabled', false);
            $('.review-button').removeClass('disabled').prop('disabled', false);
            $('.submit-button').removeClass('disabled').prop('disabled', false);
        }
        else {
            $('.configure-notifications-button').addClass('disabled').prop('disabled', false);

            $('.set-filters-button').addClass('disabled').prop('disabled', false);
            $('.review-button').addClass('disabled').prop('disabled', false);
            $('.submit-button').addClass('disabled').prop('disabled', false);
        }

    },

    _checkChooseAlertForm: function() {
        var publisherId = $("#id_publisher_id option:selected").val();
        var reportId = $("#id_report_id").val();

        if (publisherId && reportId) {
            $('.configure-notifications-button').removeClass('disabled').prop('disabled', false);

            // just for now...
            $('.set-filters-button').removeClass('disabled').prop('disabled', false);
            $('.review-button').removeClass('disabled').prop('disabled', false);
            $('.submit-button').removeClass('disabled').prop('disabled', false);
        }
        else {
            $('.configure-notifications-button').addClass('disabled').prop('disabled', false);

            // just for now...
            $('.set-filters-button').addClass('disabled').prop('disabled', false);
            $('.review-button').addClass('disabled').prop('disabled', false);
            $('.submit-button').addClass('disabled').prop('disabled', false);
        }
    },

    _checkConfigureNotificationsForm: function() {
        var name = $('#id_name').val();
        var emails = $('#id_comma_separated_emails').val();

        // if (name && emails) {
        //     $('.set-filters-button').removeClass('disabled').prop('disabled', false);
        // }
        // else {
        //     $('.set-filters-button').addClass('disabled').prop('disabled', false);
        // }
    },

    _checkSetFiltersForm: function() {
        // $('.review-button').removeClass('disabled').prop('disabled', false);
    },

    _checkReviewForm: function() {
        // $('.save-button').removeClass('disabled').prop('disabled', false);
    }
});
