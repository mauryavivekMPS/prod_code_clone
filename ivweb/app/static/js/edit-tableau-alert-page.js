$.widget("custom.edittableaualertpage", {
    options: {
        reportChoicesUrl: '',
        trustedReportUrl: '',
        selectedPublisher: null,
        selectedReport: null
    },

    _create: function() {
        var self = this;

        this.filters = {};

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

        var publisherMenu = $('#id_publisher_id');

        var nullPublisherItem = publisherMenu.find('option:first-child');
        nullPublisherItem.attr('disabled', 'disabled');
        if (!this.options.selectedPublisher) {
            publisherMenu.addClass('placeholder');
            nullPublisherItem.attr('selected', 'selected');
        }

        publisherMenu.on('change', function() {
            var selectedOption = publisherMenu.find('option:selected');
            if (!selectedOption.attr('disabled')) {
                publisherMenu.removeClass('placeholder');
                self._updateReportChoices();
            }
            self._checkForm();
        });

        var allSteps = $('.wizard-step');
        $('.choose-alert-button').on('click', function() {
            allSteps.hide();
            $('#step-choose-alert').show();
            $('.choose-alert-tab').addClass('active').siblings().removeClass('active');

        });
        $('.set-parameters-button').on('click', function() {
            allSteps.hide();
            $('#step-set-parameters').show();
            $('.set-parameters-tab').addClass('active').siblings().removeClass('active');

        });
        $('.configure-notifications-button').on('click', function() {
            allSteps.hide();
            $('#step-configure-notifications').show();
            $('.configure-notifications-tab').addClass('active').siblings().removeClass('active');

        });
        $('.set-filters-button').on('click', function() {
            allSteps.hide();
            $('#step-set-filters').show();
            $('.set-filters-tab').addClass('active').siblings().removeClass('active');

        });
        $('.review-button').on('click', function() {
            allSteps.hide();
            $('#step-review').show();
            $('.review-tab').addClass('active').siblings().removeClass('active');

        });

        this._checkForm();
    },

    _updateReportChoices: function() {
        var self = this;

        var data = [
            {name: 'publisher_id', value: $('#id_publisher_id option:selected').val()}
        ];

        $.get(this.options.reportChoicesUrl, data)
            .done(function(html) {
                $('.report-choices-control-container').html(html);

                // var reportMenu = $('#id_report_id');

                // var nullReportItem = reportMenu.find('option:first-child');
                // nullReportItem.attr('disabled', 'disabled');
                // if (!self.options.selectedReport) {
                //     reportMenu.addClass('placeholder');
                //     nullReportItem.attr('selected', 'selected');
                // }
                //
                // reportMenu.on('change', function() {
                //     var selectedOption = reportMenu.find('option:selected');
                //     if (!selectedOption.attr('disabled')) {
                //         reportMenu.removeClass('placeholder');
                //         self._updateEmbeddedReport();
                //     }
                //     self._checkForm();
                // });

                $('.report-choice-list li').on('click', function() {
                    var selectedItem = $(this);
                    selectedItem.addClass('selected').siblings().removeClass('selected');
                    var selectedReportId = selectedItem.attr('report_id');
                    $('#id_report_id').val(selectedReportId);
                    self._updateEmbeddedReport();
                })
            });
    },

    _updateEmbeddedReport: function() {
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
                            $('#id_report_params').val(JSON.stringify(self.filters));
                        });
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
    },

    _checkForm: function() {
        var publisherId = $("#id_publisher_id option:selected").val();
        var reportId = $("#id_report_id option:selected").val();
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

        if (publisherId && reportId && name && emails) {
            $('.submit-button').removeClass('disabled').prop('disabled', false);
        }
        else {
            $('.submit-button').addClass('disabled').prop('disabled', false);
        }
    }
});
