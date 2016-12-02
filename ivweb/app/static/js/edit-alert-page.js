$.widget("custom.editalertpage", {
    options: {
        alertParamsUrl: '',
        alertFiltersUrl: '',
        checkChoicesUrl: '',
        trustedReportUrl: '',
        selectedAlertType: null,
        selectedReportType: null,
        selectedCheck: null,
        initialFilters: {},
        initialParams: {}
    },

    _create: function() {
        var self = this;

        this.params = [];
        this.filters = [];

        $('#id_publisher_id').on('change', function() {
            self._updateCheckChoices();
        });
        if (!this.options.selectedCheck) {
            this._updateCheckChoices();
        }
        this._wireUpCheckChoices();

        $('#id_name, #id_comma_separated_emails').on('keyup', function() {
            self._checkForm();
        });

        $('#id_enabled').on('change', function() {
            self._checkForm();
        });

        var m = $('#confirm-archive-alert-modal');

        m.find('.confirm-archive-alert-button').on('click', function() {
            IvetlWeb.showLoading();
            m.modal('hide');
            $('#archive-alert-form').submit();
        });

        $('.archive-alert').on('click', function () {
            m.modal();
        });

        this._setFilters(this.options.initialFilters);
        this._setParams(this.options.initialParams);
        this._checkForm();

        var alertTypeMenu = $('#id_alert_type');

        var nullAlertTypeItem = alertTypeMenu.find('option:first-child');
        nullAlertTypeItem.attr('disabled', 'disabled');
        if (!this.options.selectedAlertType) {
            alertTypeMenu.addClass('placeholder');
            nullAlertTypeItem.attr('selected', 'selected');
        }

        alertTypeMenu.on('change', function() {
            self._updateAlertTypeMenu();
        });

        var reportTypeMenu = $('#id_report_type');

        var nullReportTypeItem = reportTypeMenu.find('option:first-child');
        nullReportTypeItem.attr('disabled', 'disabled');
        if (!this.options.selectedReportType) {
            reportTypeMenu.addClass('placeholder');
            nullReportTypeItem.attr('selected', 'selected');
        }

        reportTypeMenu.on('change', function() {
            self._updateReportTypeMenu();
        });
    },

    _updateAlertTypeMenu: function() {
        var alertTypeMenu = $('#id_alert_type');
        var selectedOption = alertTypeMenu.find('option:selected');
        if (!selectedOption.attr('disabled')) {
            alertTypeMenu.removeClass('placeholder');

            var selectedType = selectedOption.val();
            if (selectedType == 'scheduled') {
                $('.threshold-alert-controls').hide();
                $('.scheduled-alert-controls').show();
            }
            else if (selectedType == 'threshold') {
                $('.scheduled-alert-controls').hide();
                $('.threshold-alert-controls').show();
            }
            else {
                $('.scheduled-alert-controls').hide();
                $('.threshold-alert-controls').hide();
            }
        }
    },

    _updateReportTypeMenu: function() {
        var reportTypeMenu = $('#id_report_type');
        var selectedOption = reportTypeMenu.find('option:selected');
        if (!selectedOption.attr('disabled')) {
            reportTypeMenu.removeClass('placeholder');

            var controls = $('.embedded-report-controls');
            var selectedType = selectedOption.val();
            if (selectedType != '') {

                var data = {
                    'report': selectedType
                };

                IvetlWeb.showLoading();

                $.get(this.options.trustedReportUrl, data)
                    .done(function (response) {
                        var trustedReportUrl = response.url;
                        console.log('trusted URL: ' + trustedReportUrl);
                        controls.show();
                        var reportContainer = controls.find('.embedded-report-container')[0];
                        new tableau.Viz(reportContainer, trustedReportUrl, {
                            width: reportContainer.offsetWidth,
                            height: reportContainer.offsetHeight,
                            hideTabs: true,
                            hideToolbar: true,
                            onFirstInteractive: function () {
                                // var workbook = viz.getWorkbook();
                                // var activeSheet = workbook.getActiveSheet();
                            }
                        });
                    })
                    .always(function () {
                        IvetlWeb.hideLoading();
                    });

                // var trustedReportUrl = "http://public.tableau.com/views/WorldIndicators/GDPpercapita";
            }
            else {
                controls.hide();
            }
        }
    },

    _isIntegerValue: function(value) {
        return !isNaN(value) && parseInt(Number(value)) == value && !isNaN(parseInt(value, 10)) && parseInt(value) > 0;
    },

    _isFloatValue: function(value) {
      return !isNaN(parseFloat(value)) && isFinite(value);
    },

    _isPercentageIntegerValue: function(value) {
        return self._isIntegerValue(value) && parseInt(value) > 0;
    },

    _isPercentageFloatValue: function(value) {
        return self._isFloatValue(value) && parseFloat(value) > 0;
    },

    _checkForm: function() {
        var checkId = $("#id_check_id option:selected").val();
        var publisherId = $("#id_publisher_id option:selected").val();
        var name = $('#id_name').val();
        var emails = $('#id_comma_separated_emails').val();

        if (name) {
            $('.name-requirement').addClass('satisfied');
        }
        else {
            $('.name-requirement').removeClass('satisfied');
        }

        if (emails) {
            $('.email-requirement').addClass('satisfied');
        }
        else {
            $('.email-requirement').removeClass('satisfied');
        }

        var gotParamValues = true;
        $.each(this.params, function(index, param) {
            var requirement = $('.' + param.name + '-requirement');
            var value = $('#id_param_' + param.name).val();

            var isValid = false;
            if (value) {
                if (param.type == 'integer') {
                    isValid = self._isIntegerValue(value);
                }
                else if (param.type == 'float') {
                    isValid = self._isFloatValue(value);
                }
                else if (param.type == 'percentage-integer') {
                    isValid = self._isPercentageIntegerValue(value);
                }
                else if (param.type == 'percentage-float') {
                    isValid = self._isPercentageFloatValue(value);
                }
            }

            if (value && isValid) {
                requirement.addClass('satisfied');
            }
            else {
                requirement.removeClass('satisfied');
                gotParamValues = false;
            }
        });

        if (publisherId && checkId && name && emails && gotParamValues) {
            $('.submit-button').removeClass('disabled').prop('disabled', false);
        }
        else {
            $('.submit-button').addClass('disabled').prop('disabled', false);
        }
    },

    _setParams: function(newParams) {
        var self = this;
        this.params = newParams;
        $.each(this.params, function(index, param) {
            $('.requirements-items .param-requirement').remove();
            $('.requirements-items').append('<li class="' + param.name + '-requirement param-requirement">' + param.requirement_text + '<span class="lnr lnr-check checkmark"></span></li>');
            $('#id_param_' + param.name).on('keyup', function() {
                self._checkForm();
            });
        });
    },

    _setFilters: function(newFilters) {
        var self = this;
        this.filters = newFilters;
        $.each(this.filters, function(index, filter) {
            var filterElement = $('#id_filter_' + filter.name);

            filterElement.typeahead({
                source: filter.filter_values,
                showHintOnFocus: true,
                autoSelect: true
            });

            filterElement.on('keyup', function() {
                self._checkForm();
            });
        });
    },

    _updateFilters: function() {
        var self = this;
        var checkId = $('#id_check_id option:selected').val();
        var publisherId = $("#id_publisher_id option:selected").val();

        var data = [
            {name: 'check_id', value: checkId},
            {name: 'publisher_id', value: publisherId}
        ];

        IvetlWeb.showLoading();

        $.get(this.options.alertFiltersUrl, data)
            .done(function(response) {
                $('.alert-filters').html(response.html);
                self._setFilters(response.filters)
            })
            .always(function() {
                IvetlWeb.hideLoading();
            });
    },

    _onPublisherOrCheckChange: function() {
        if ($('#id_check_id option').length > 0) {
            this._updateParams();
            this._updateFilters();
        }
        else {
            $('#id_name').val('');
        }
        this._checkForm();
    },

    _wireUpCheckChoices: function() {
        var self = this;
        $('#id_check_id').on('change', function() {
            self._onPublisherOrCheckChange();
        });
    },

    _updateCheckChoices: function() {
        var self = this;

        var data = [
            {name: 'publisher_id', value: $('#id_publisher_id option:selected').val()}
        ];

        $.get(this.options.checkChoicesUrl, data)
            .done(function(html) {
                $('.check-control-container').html(html);
                self._wireUpCheckChoices();
                self._onPublisherOrCheckChange();
            });
    },

    _updateParams: function() {
        var self = this;
        var checkId = $('#id_check_id option:selected').val();

        $(this).removeClass('placeholder');

        var data = [
            {name: 'check_id', value: checkId}
        ];

        IvetlWeb.showLoading();
        $.get(this.options.alertParamsUrl, data)
            .done(function(response) {
                $('.alert-params').html(response.html);
                self._setParams(response.params);
            })
            .always(function() {
                IvetlWeb.hideLoading();
            });
    },
});
