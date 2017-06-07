$.widget("custom.externalnotificationreportpage", {
    options: {
        trustedReportUrl: '',
        publisherId: '',
        alertTemplateId: '',
        filterWorksheetName: '',
        filters: {},
        params: {}
    },

    _create: function () {
        var self = this;
        var data = {
            template_id: this.options.alertTemplateId,
            publisher_id: this.options.publisherId,
            embed_type: 'full'
        };
        $.get(this.options.trustedReportUrl, data)
            .done(function (response) {
                var trustedReportUrl = response.url;
                var reportContainer = $('.embedded-report-container')[0];

                var allExistingFilters = self.options.filters;
                var allExistingParameters = self.options.params;

                var vizOptions = {
                    hideTabs: false,
                    hideToolbar: true,
                    onFirstInteractive: function () {
                        var workbook = viz.getWorkbook();
                        var activeSheet = workbook.getActiveSheet();

                        if (activeSheet.getSheetType() !== 'worksheet') {
                            var allWorksheets = activeSheet.getWorksheets();
                            for (var i = 0; i < allWorksheets.length; i++) {
                                var worksheet = allWorksheets[i];
                                if (worksheet.getName() === self.options.filterWorksheetName) {
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

                        // ranges and excluded values get applied after load
                        $.each(Object.keys(allExistingFilters), function (index, name) {
                            var filter = allExistingFilters[name];

                            if (filter.type === 'categorical' && filter.exclude) {
                                activeSheet.applyFilterAsync(name, filter.values, tableauSoftware.FilterUpdateType.REMOVE);
                            }
                            else if (filter.type === 'quantitative') {
                                var minDate = new Date(filter.min);
                                var maxDate = new Date(filter.max);
                                activeSheet.applyRangeFilterAsync(name, {min: minDate, max: maxDate})
                                    .otherwise(function (err) {
                                        console.log('Error setting range filter: ' + err);
                                    });
                            }
                        });
                    }
                };

                $.each(Object.keys(allExistingFilters), function (index, name) {
                    var filter = allExistingFilters[name];
                    if (filter.type === 'categorical' && !filter.exclude) {
                        vizOptions[name] = [];
                        $.each(filter.values, function (index, value) {
                            vizOptions[name].push(value);
                        });
                    }
                });

                var viz = new tableau.Viz(reportContainer, trustedReportUrl, vizOptions);

                $('.export-image-button').on('click', function (e) {
                    viz.showExportImageDialog();
                    e.preventDefault();
                });

                $('.export-pdf-button').on('click', function (e) {
                    viz.showExportPDFDialog();
                    e.preventDefault();
                });

                $('.export-crosstab-button').on('click', function (e) {
                    viz.showExportCrossTabDialog();
                    e.preventDefault();
                });
            })
            .always(function () {
                IvetlWeb.hideLoading();
            });
    }
});
