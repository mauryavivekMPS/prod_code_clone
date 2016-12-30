$.widget("custom.externalnotificationreportpage", {
    options: {
        trustedReportUrl: '',
        alertTemplateId: '',
        filters: {}
    },

    _create: function() {
        var self = this;
        $.get(this.options.trustedReportUrl, {template_id: self.options.alertTemplateId, embed_type: 'full'})
            .done(function (response) {
                var trustedReportUrl = response.url;
                var reportContainer = $('.embedded-report-container')[0];

                var vizOptions = {
                    hideTabs: false,
                    hideToolbar: true
                };

                // apply each of the filters
                $.each(Object.keys(self.options.filters), function(index, name) {
                    vizOptions[name] = [];
                    $.each(self.options.filters[name], function(index, value) {
                        vizOptions[name].push(value);
                    });
                });

                var viz = new tableau.Viz(reportContainer, trustedReportUrl, vizOptions);

                // viz.addEventListener(tableau.TableauEventName.FILTER_CHANGE, function(e) {
                //     e.getFilterAsync().then(function(filter) {
                //         self.filters[filter._caption] = [];
                //         var selectedValues = filter.getAppliedValues();
                //         $.each(selectedValues, function(index, value) {
                //             self.filters[filter._caption].push(value.value);
                //         });
                //         $('#id_report_params').val(JSON.stringify(self.filters));
                //     });
                // });
            })
            .always(function () {
                IvetlWeb.hideLoading();
            });
    }
});
