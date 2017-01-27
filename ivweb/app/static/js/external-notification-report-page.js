$.widget("custom.externalnotificationreportpage", {
    options: {
        trustedReportUrl: '',
        publisherId: '',
        alertTemplateId: '',
        filters: {}
    },

    _create: function() {
        var self = this;
        var data = {
            template_id: self.options.alertTemplateId,
            publisher_id: self.options.publisherId,
            embed_type: 'full'
        };
        $.get(this.options.trustedReportUrl, data)
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
            })
            .always(function () {
                IvetlWeb.hideLoading();
            });
    }
});
