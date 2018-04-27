var FileUploadWidget = (function() {
    var publisherId;
    var demoId;
    var uploadUrl;
    var deleteUrl;
    var csrfToken;
    var isDemo;

    var wireUpDeleteButtons = function(selector) {
        $(selector).each(function() {
            var link = $(this);
            link.click(function() {
                var productId = link.attr('product_id');
                var pipelineId = link.attr('pipeline_id');
                var fileToDelete = link.attr('file_to_delete');
                var fileId = link.closest('tr.file-row').attr('file_id');

                var data = [
                    {name: 'csrfmiddlewaretoken', value: csrfToken},
                    {name: 'file_to_delete', value: fileToDelete},
                    {name: 'product_id', value: productId},
                    {name: 'pipeline_id', value: pipelineId}
                ];

                if (isDemo) {
                    data.push({name: 'file_type', value: 'demo'});
                    data.push({name: 'demo_id', value: demoId});
                }
                else {
                    data.push({name: 'file_type', value: 'publisher'});
                    data.push({name: 'publisher_id', value: publisherId});
                }

                $.post(deleteUrl, data)
                    .always(function() {
                        var row = link.closest('tr');
                        row.fadeOut(150, function() {
                            $('.file-row.file-row-' + fileId).remove();
                            $('.error-list-row.file-row-' + fileId).remove();
                            $('.loading-row.file-row-' + fileId).remove();
                            updateTable();
                            PendingFilesForm.updateSubmitForProcessing();

                            if (isDemo) {
                                EditPublisherPage.checkForm();
                            }

                        });
                        IvetlWeb.hideLoading();
                    });

                return false;
            });
        });
    };

    var wireUpFilePickers = function(selector) {
        $(selector).on('change', function() {
            var picker = $(this);
            if (picker.val()) {
                var f = $(this.form)[0];
                var data = new FormData(f);
                var pickerRow;
                var loadingWidget;

                if (isDemo) {
                    data.append('crossref_username', $('#id_crossref_username'));
                    data.append('crossref_password', $('#id_crossref_password'));

                    var issns = [];
                    $('.issn-values-row').each(function() {
                        var row = $(this);
                        var index = row.attr('index');
                        issns.push({
                            electronic_issn: row.find('#id_electronic_issn_' + index).val(),
                            print_issn: row.find('#id_print_issn_' + index).val()
                        });
                    });
                    data.append('issns', JSON.stringify(issns));
                }

                var uiType = picker.attr('ui_type');
                if (uiType === 'replacement') {
                    var fileId = picker.closest('tr.error-list-row').attr('file_id');
                    $('.file-row.file-row-' + fileId).remove();
                    $('.error-list-row.file-row-' + fileId).remove();
                    $('.loading-row.file-row-' + fileId).show();
                }
                else {
                    $(f).hide();
                    pickerRow = picker.closest('tr.upload-another-row');
                    loadingWidget = pickerRow.find('.inline-upload-form-loading');
                    loadingWidget.show();
                }

                $.ajax(uploadUrl, {type: 'POST', data: data, contentType: false, processData: false})
                    .done(function(html) {
                        if (uiType === 'replacement') {
                            $('.loading-row.file-row-' + fileId).replaceWith(html);
                        }
                        else {
                            pickerRow.before(html);
                            loadingWidget.hide();
                            picker.val('');
                            $(f).show();
                        }
                    })
                    .always(function() {
                        EditPublisherPage.checkForm();
                    });
            }
        });
    };

    var updateTable = function() {
        if (!isDemo) {
            var table = $('table.all-files-table');
            if (table.find('> tbody > tr').length == 1) {
                table.addClass('no-files');
                table.removeClass('has-files');
            }
            else {
                table.addClass('has-files');
                table.removeClass('no-files');
            }
        }
    };

    var init = function(options) {
        options = $.extend({
            publisherId: '',
            demoId: '',
            uploadUrl: '',
            deleteUrl: '',
            isDemo: false,
            csrfToken: ''
        }, options);

        publisherId = options.publisherId;
        demoId = options.demoId;
        uploadUrl = options.uploadUrl;
        deleteUrl = options.deleteUrl;
        csrfToken = options.csrfToken;
        isDemo = options.isDemo;

        wireUpDeleteButtons('.delete-file-button');
        wireUpFilePickers('.replacement-file-picker');
        updateTable();
    };

    return {
        wireUpDeleteButtons: wireUpDeleteButtons,
        wireUpFilePickers: wireUpFilePickers,
        updateTable: updateTable,
        init: init
    };

})();
