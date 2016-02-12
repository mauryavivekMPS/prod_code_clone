//
// Common app functions
//

var IvetlWeb = (function() {
    var loading = $('#loading');
    var loadingMessage = $('#loading-message');
    var loadingMessageTimer;

    var showLoading = function() {
        if (loadingMessageTimer) {
            clearTimeout(loadingMessageTimer);
            loadingMessageTimer = null;
            loadingMessage.empty();
        }
        loading.fadeIn(330);
    };

    var hideLoading = function(message) {
        loading.fadeOut(150, function() {
            if (message) {
                loadingMessage.html(message).fadeIn(150, function() {
                    loadingMessageTimer = setTimeout(function() {
                        loadingMessage.fadeOut(150, function() {
                            loadingMessage.empty();
                        });
                        loadingMessageTimer = null;
                    }, 3000);
                });
            }
        });
    };

    var initTooltips = function(baseSelector) {
        $(baseSelector + ' ' + '[data-toggle="tooltip"]').tooltip();
    };

    var setPageClasses = function(htmlClass, bodyClass) {
        $('html').removeClass().addClass(htmlClass);
        $('body').removeClass().addClass('meerkat ' + bodyClass);
    };

    var resetUrl = function(url) {
        history.replaceState({}, "", url);
    };

    var hideMessagesAfterDelay = function() {
        setTimeout(function() {
            hideMessages();
        }, 10000);

    };

    var hideMessages = function() {
        $('.messages-container').fadeOut(400);
    };

    var hideErrorsAfterDelay = function() {
        setTimeout(function() {
            hideErrors();
        }, 5000);
    };

    var hideErrors = function(immediate) {
        $('.errors-container').fadeOut(400);
    };

    return {
        showLoading: showLoading,
        hideLoading: hideLoading,
        initTooltips: initTooltips,
        setPageClasses: setPageClasses,
        resetUrl: resetUrl,
        hideMessagesAfterDelay: hideMessagesAfterDelay,
        hideMessages: hideMessages,
        hideErrorsAfterDelay: hideErrorsAfterDelay,
        hideErrors: hideErrors
    };

})();


//
// Pipeline detail page
//

var PipelineListPage = (function() {
    var pipelineId = '';
    var csrfToken = '';
    var updatePublisherUrl = '';
    var tailUrl = '';
    var runForPublisherUrl = '';
    var runForAllUrl = '';
    var isSuperuser = false;
    var tailIntervalIds = {};
    var publisherTaskStatus = {};
    var pipelineName = '';

    var updateRunButton = function() {
        var somethingIsRunning = false;
        $.each(publisherTaskStatus, function(publisherId) {
            if (publisherTaskStatus[publisherId] == 'in-progress') {
                somethingIsRunning = true;
                return false;
            }
        });
        if (somethingIsRunning) {
            $('.run-button').hide();
        }
        else {
            $('.run-button').show();
        }
    };

    var updatePublisher = function(publisherId) {
        var summaryRow = $('.' + publisherId + '_summary_row');
        var opened = 0;
        if ($('.' + publisherId + '_opener').is(':visible')) {
            opened = 1;
        }
        var data = [
            {name: 'csrfmiddlewaretoken', value: csrfToken},
            {name: 'publisher_id', value: publisherId},
            {name: 'current_job_id', value: summaryRow.attr('current_job_id')},
            {name: 'current_task_id', value: summaryRow.attr('current_task_id')},
            {name: 'current_task_status', value: summaryRow.attr('current_task_status')},
            {name: 'opened', value: opened}
        ];

        $.getJSON(updatePublisherUrl, data)
            .done(function(json) {

                // replace the entire publisher section if we've got a task-level update
                if (json.has_section_updates) {
                    $('.' + publisherId + '_row').remove();
                    summaryRow.replaceWith(json.publisher_details_html);
                    wirePublisherLinks('.' + publisherId + '_summary_row .publisher-link');
                    wireRunForPublisherForms('.' + publisherId + '_summary_row .run-pipeline-for-publisher-inline-form');
                    wireTaskLinks('.' + publisherId + '_row .task-link');

                    // store this publisher status and update the main run button
                    var newSummaryRow = $('.' + publisherId + '_summary_row');
                    publisherTaskStatus[publisherId] = newSummaryRow.attr('current_task_status');
                    updateRunButton();
                }

                // update the progress bar
                if (json.has_progress_bar_updates) {
                    var progressBarContainer = $('.' + publisherId + '_row .task-progress');
                    var progressBar = progressBarContainer.find('.progress-bar');
                    var newTitle = 'Processing ' + json.current_record_count + ' of ' + json.total_record_count + ' records';
                    progressBarContainer.attr('data-original-title', newTitle);
                    progressBar.css('width', json.percent_complete + '%');
                    IvetlWeb.initTooltips('.' + publisherId + '_row');
                }
            });

        // start again...
        setTimeout(function() {
            updatePublisher(publisherId);
        }, 3000);
    };

    var wirePublisherLinks = function(selector) {
        $(selector).each(function() {
            var link = $(this);
            link.click(function() {
                var publisherId = link.attr('publisher_id');
                var openerIcon = $('.' + publisherId + '_opener');
                var closerIcon = $('.' + publisherId + '_closer');

                // use the icon to figure out if open or closed
                if (openerIcon.is(':visible')) {
                    $('.' + publisherId + '_row').fadeOut(100);
                    $('.' + publisherId + '_summary_row .summary-value').fadeIn(100);
                    openerIcon.hide();
                    closerIcon.show();
                }
                else {
                    $('.' + publisherId + '_row:not(.tail-row)').fadeIn(200);
                    $('.' + publisherId + '_summary_row .summary-value').fadeOut(100);
                    closerIcon.hide();
                    openerIcon.show();
                }
                return false;
            });
        });
    };

    var wireRunForPublisherForms = function(selector) {
        $(selector).submit(function(event) {
            var form = $(this);
            var publisherName = form.attr('publisher_name');

            // update the modal and open it
            var m = $('#confirm-run-single-modal');
            m.find('.modal-title').html('Run Pipeline for Publisher');
            m.find('.modal-body').html('<p>Are you sure you want to run the ' + pipelineName + ' pipeline for <span style="font-weight:600">' + publisherName + '</span>?</p>');

            var submitButton = m.find('.confirm-run-single-submit-button');
            submitButton.on('click', function() {
                submitButton.off('click');
                m.off('hidden.bs.modal');
                m.modal('hide');

                form.find('.run-pipeline-for-publisher-button').hide();
                form.find('.run-loading-icon').show();
                var parent = form.parent();
                parent.find('.little-upload-button').hide();
                parent.find('.little-files-link').hide();
                $('.run-button').hide();
                $.post(runForPublisherUrl, form.serialize());
            });
            m.modal();

            m.on('hidden.bs.modal', function () {
                submitButton.off('click');
                m.off('hidden.bs.modal');
            });

            event.preventDefault();
            return false;
        });
    };

    var wireTaskLinks = function(selector) {
        $(selector).each(function() {
            var link = $(this);
            link.click(function() {
                var publisherId = link.attr('publisher_id');
                var jobId = link.attr('job_id');
                var taskId = link.attr('task_id');
                var tailRow = $('.' + publisherId + '_' + jobId + '_' + taskId + '_row');
                if (tailRow.is(':visible')) {
                    tailRow.fadeOut(100);
                }
                else {
                    var data = [
                        {name: 'csrfmiddlewaretoken', value: csrfToken},
                        {name: 'publisher_id', value: publisherId},
                        {name: 'job_id', value: jobId},
                        {name: 'task_id', value: taskId}
                    ];

                    $.get(tailUrl, data)
                        .done(function(text) {
                            var pre = tailRow.find('.tail-output pre');
                            pre.empty().text(text);
                        })
                        .always(function() {
                            tailRow.fadeIn(200);
                            var pre = tailRow.find('.tail-output pre');
                            pre.scrollTop(pre[0].scrollHeight);
                        });
                }
                return false;
            });
        });
    };

    var startTailForPublisher = function(publisherId) {
        var summaryRow = $('.' + publisherId + '_summary_row');
        var jobId = summaryRow.attr('current_job_id');
        var taskId = summaryRow.attr('current_task_id');
        var key = publisherId + '_' + jobId + '_' + taskId;
        var tailRow = $('.' + key + '_row');
        var output = tailRow.find('.tail-output');

        output.addClass('live');
        var pre = output.find('pre');
        var tailInterval = setInterval(function() {

            var existingLog = pre.text().trimRight();
            var lastLine = '';
            if (existingLog != '') {
                lastLine = existingLog.slice(existingLog.lastIndexOf('\n') + 1);
            }

            var data = [
                {name: 'csrfmiddlewaretoken', value: csrfToken},
                {name: 'publisher_id', value: publisherId},
                {name: 'job_id', value: jobId},
                {name: 'task_id', value: taskId},
                {name: 'last_line', value: lastLine}
            ];

            $.get(tailUrl, data)
                .done(function(text) {
                    pre.append(text);
                })
                .always(function() {
                    pre.scrollTop(pre[0].scrollHeight);
                });

        }, 1000);
        tailIntervalIds[publisherId] = tailInterval;
    };

    var cancelTailForPublisher = function(publisherId) {
        clearInterval(tailIntervalIds[publisherId]);
        var summaryRow = $('.' + publisherId + '_summary_row');
        var jobId = summaryRow.attr('current_job_id');
        var taskId = summaryRow.attr('current_task_id');
        var key = publisherId + '_' + jobId + '_' + taskId;
        $('.' + key + '_row .tail-output').removeClass('live');
    };

    var init = function(options) {
        options = $.extend({
            pipelineId: '',
            publishers: [],
            tailUrl: '',
            updatePublisherUrl: '',
            runForPublisherUrl: '',
            runForAllUrl: '',
            isSuperuser: false,
            csrfToken: '',
            pipelineName: ''
        }, options);

        pipelineId = options.pipelineId;
        csrfToken = options.csrfToken;
        updatePublisherUrl = options.updatePublisherUrl;
        runForPublisherUrl = options.runForPublisherUrl;
        runForAllUrl = options.runForAllUrl;
        tailUrl = options.tailUrl;
        isSuperuser = options.isSuperuser;
        pipelineName = options.pipelineName;

        if (isSuperuser) {
            var m = $('#confirm-run-all-modal');
            $('.run-button').click(function() {
                m.modal();
            });

            $('#confirm-run-all-modal .confirm-run-all-modal-submit-button').click(function() {
                m.modal('hide');
                $('.run-button').hide();
                var loading = $('.run-for-all-loading-icon');
                loading.show();
                setTimeout(function() {
                    loading.hide();
                }, 3000);
                $('#run-pipeline-form').submit();
                return false;
            });

            wirePublisherLinks('.publisher-link');
            wireTaskLinks('.task-link');
        }

        wireRunForPublisherForms('.run-pipeline-for-publisher-inline-form');

        $.each(options.publishers, function(index, publisherId) {
            setTimeout(function() {
                updatePublisher(publisherId);
            }, 3000);
        });
    };

    return {
        init: init,
        startTailForPublisher: startTailForPublisher,
        cancelTailForPublisher: cancelTailForPublisher
    };

})();


//
// Upload page
//

var UploadPage = (function() {
    var f;
    var pipelineId = '';
    var hasPublisher;

    var checkForm = function() {
        var publisherId;
        if (!hasPublisher) {
            publisherId = f.find("#id_publisher option:selected").val();
        }
        var file = f.find("#id_files").val();

        if ((hasPublisher || publisherId) && file) {
            f.find('.submit-button').removeClass('disabled').prop('disabled', false);
        }
        else {
            f.find('.submit-button').addClass('disabled').prop('disabled', true);
        }
    };

    var init = function(options) {
        options = $.extend({
            pipelineId: '',
            hasPublisher: false
        }, options);

        f = $('#upload-form');
        pipelineId = options.pipelineId;
        hasPublisher = options.hasPublisher;

        if (!hasPublisher) {
            var publisherMenu = f.find('#id_publisher');
            var nullPublisherItem = publisherMenu.find('option:first-child');
            nullPublisherItem.attr('disabled', 'disabled');
            if (!options.selectedPublisher) {
                publisherMenu.addClass('placeholder');
                nullPublisherItem.attr('selected', 'selected');
            }

            publisherMenu.on('change', function () {
                var selectedOption = publisherMenu.find("option:selected");
                if (!selectedOption.attr('disabled')) {
                    publisherMenu.removeClass('placeholder');
                }
                checkForm();
            });
        }

        f.find('#id_files').on('change', checkForm);

        f.submit(function() {
            IvetlWeb.showLoading();
        });
    };

    return {
        init: init
    };

})();












//
// File upload widget
//

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
                        });
                        IvetlWeb.hideLoading();
                    });

                return false;
            });
        });
    };

    var wireUpFilePickers = function(selector) {
        $(selector).on('change', function() {
            //var picker = $(this);
            //if (picker.val()) {
            //    var f = $(this.form)[0];
            //    var data = new FormData(f);
            //
            //    var parentRow = picker.closest('tr.error-list-row');
            //    var fileId = parentRow.attr('file_id');
            //
            //    $('.file-row.file-row-' + fileId).remove();
            //    $('.error-list-row.file-row-' + fileId).remove();
            //    $('.loading-row.file-row-' + fileId).show();
            //
            //    $.ajax(uploadUrl, {type: 'POST', data: data, contentType: false, processData: false})
            //        .done(function(html) {
            //            console.log('done');
            //            $('.loading-row.file-row-' + fileId).replaceWith(html);
            //        })
            //        .always(function() {
            //            console.log('always');
            //        });
            //}
        });
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

    };

    return {
        wireUpDeleteButtons: wireUpDeleteButtons,
        wireUpFilePickers: wireUpFilePickers,
        init: init
    };

})();













//
// Pending files form
//

var PendingFilesForm = (function() {
    var pipelineId = '';
    var publisherId = '';
    var deleteUrl = '';
    var csrfToken = '';

    var wireUpDeleteButtons = function(selector) {
        $(selector).each(function() {
            var link = $(this);
            link.click(function() {
                var fileToDelete = link.attr('file_to_delete');
                var data = [
                    {name: 'csrfmiddlewaretoken', value: csrfToken},
                    {name: 'publisher', value: publisherId},
                    {name: 'file_to_delete', value: fileToDelete}
                ];

                $.post(deleteUrl, data)
                    .always(function() {
                        var row = link.closest('tr');
                        row.fadeOut(150, function() {
                            row.remove();
                        });
                        IvetlWeb.hideLoading();
                    });

                return false;
            });
        });

    };

    var init = function(options) {
        options = $.extend({
            pipelineId: '',
            publisherId: '',
            deleteUrl: '',
            csrfToken: ''
        }, options);

        pipelineId = options.pipelineId;
        publisherId = options.publisherId;
        deleteUrl = options.deleteUrl;
        csrfToken = options.csrfToken;

        wireUpDeleteButtons('.delete-file-button');
    };

    return {
        wireUpDeleteButtons: wireUpDeleteButtons,
        init: init
    };

})();


//
// Upload Results page
//

var UploadResultsPage = (function() {
    var uploadUrl;

    var wireUpFilePickers = function(selector) {
        $(selector).on('change', function() {
            var picker = $(this);
            if (picker.val()) {
                var f = $(this.form)[0];
                var data = new FormData(f);

                var parentRow = picker.closest('tr.error-list-row');
                var fileId = parentRow.attr('file_id');

                $('.file-row.file-row-' + fileId).remove();
                $('.error-list-row.file-row-' + fileId).remove();
                $('.loading-row.file-row-' + fileId).show();

                $.ajax(uploadUrl, {type: 'POST', data: data, contentType: false, processData: false})
                    .done(function(html) {
                        console.log('done');
                        $('.loading-row.file-row-' + fileId).replaceWith(html);
                    })
                    .always(function() {
                        console.log('always');
                    });
            }
        });
    };

    var init = function(options) {
        options = $.extend({
            uploadUrl: ''
        }, options);

        uploadUrl = options.uploadUrl;

        wireUpFilePickers('.replacement-file-picker');
    };

    return {
        wireUpFilePickers: wireUpFilePickers,
        init: init
    };

})();


//
// Run page
//

var RunPage = (function() {
    var f;
    var pipelineId = '';

    var checkForm = function() {
        var publisherId = f.find("#id_publisher option:selected").val();
        if (publisherId) {
            f.find('.submit-button').removeClass('disabled').prop('disabled', false);
        }
        else {
            f.find('.submit-button').addClass('disabled').prop('disabled', false);
        }
    };

    var init = function(options) {
        options = $.extend({
            pipelineId: '',
            selectedPublisher: null
        }, options);

        f = $('#run-pipeline-for-publisher-form');
        pipelineId = options.pipelineId;

        var publisherMenu = f.find('#id_publisher');
        var nullPublisherItem = publisherMenu.find('option:first-child');
        nullPublisherItem.attr('disabled', 'disabled');
        if (!options.selectedPublisher) {
            publisherMenu.addClass('placeholder');
            nullPublisherItem.attr('selected', 'selected');
        }

        publisherMenu.on('change', function() {
            var selectedOption = publisherMenu.find("option:selected");
            if (!selectedOption.attr('disabled')) {
                publisherMenu.removeClass('placeholder');
            }
            checkForm();
        });

        f.submit(function() {
            IvetlWeb.showLoading();
        });
    };

    return {
        init: init
    };

})();


//
// Edit Publisher page
//

var EditPublisherPage = (function() {
    var publisherId;
    var isNew;
    var validateCrossrefUrl;
    var validateIssnUrl;
    var addIssnValuesUrl;
    var buildingPollUrl;
    var buildingSuccessUrl;
    var buildingErrorUrl;
    var csrfToken;
    var isDemo;

    var enableSubmit = function() {
        $('.submit-button.save-button').removeClass('disabled').prop('disabled', false);
    };

    var disableSubmit = function() {
        $('.submit-button.save-button').addClass('disabled').prop('disabled', true);
    };

    var checkForm = function() {

        // quick easy validation for saving demos
        var name = $("#id_name").val();
        var hasName = name != '';
        if (isDemo) {
            if (hasName) {
                enableSubmit();
            }
            else {
                disableSubmit();
            }
            return
        }

        // onto the non-demo validation
        var publisherId = $("#id_publisher_id").val();
        var email = $("#id_email").val();
        var hasBasics = publisherId != '' && name != '' && email != '';

        var publishedArticlesProduct = $('#id_published_articles').is(':checked');
        var rejectedManuscriptsProduct = $('#id_rejected_manuscripts').is(':checked');
        var cohortArticlesProduct = $('#id_cohort_articles').is(':checked');
        var atLeastOneProduct = publishedArticlesProduct || rejectedManuscriptsProduct || cohortArticlesProduct;

        var hasReportsDetails = true;
        if (isNew) {
            var reportsUsername = $('#id_reports_username').val();
            var reportsPassword = $('#id_reports_username').val();
            var reportsProject = $('#id_reports_project').val();
            hasReportsDetails = reportsUsername && reportsPassword && reportsProject;
        }

        var crossref = true;
        if (useCrossref()) {
            var username = $('#id_crossref_username').val();
            var password = $('#id_crossref_password').val();
            var validated = $('.validate-crossref-checkmark').is(':visible');
            crossref = username && password && validated;
        }

        var validIssns = true;
        if (publishedArticlesProduct) {
            var gotOne = false;
            $('.issn-values-row').each(function () {
                var row = $(this);
                if (row.find('.validate-issn-checkmark').is(':visible')) {
                    gotOne = true;
                }
                else {
                    if (gotOne && isIssnRowEmpty(row)) {
                        // let it slide
                    }
                    else {
                        validIssns = false;
                        return false;
                    }
                }
            });
        }

        var validCohortIssns = true;
        if (cohortArticlesProduct) {
            var gotOne = false;
            $('.issn-values-cohort-row').each(function () {
                var row = $(this);
                if (row.find('.validate-issn-checkmark').is(':visible')) {
                    gotOne = true;
                }
                else {
                    if (gotOne && isIssnRowEmpty(row)) {
                        // let it slide
                    }
                    else {
                        validCohortIssns = false;
                        return false;
                    }
                }
            });
        }

        if (hasBasics && atLeastOneProduct && hasReportsDetails && crossref && validIssns && validCohortIssns) {
            enableSubmit();
        }
        else {
            disableSubmit();
        }
    };

    var updatePublishedArticlesControls = function() {
        if ($('#id_published_articles').is(':checked')) {
            $('.published-articles-controls').fadeIn(200);
        }
        else {
            $('.published-articles-controls').fadeOut(100);
        }
    };

    var updateRejectedManuscriptsControls = function() {
        if ($('#id_rejected_manuscripts').is(':checked')) {
            $('.rejected-manuscripts-controls').fadeIn(200);
        }
        else {
            $('.rejected-manuscripts-controls').fadeOut(100);
        }
    };

    var updateCohortArticlesControls = function() {
        if ($('#id_cohort_articles').is(':checked')) {
            $('.cohort-articles-controls').fadeIn(200);
        }
        else {
            $('.cohort-articles-controls').fadeOut(100);
        }
    };

    var hasHighWire = function() {
        return $('#id_hw_addl_metadata_available').is(':checked');
    };

    var updateHighWireControls = function() {
        if (hasHighWire()) {
            $('.highwire-controls').fadeIn(200);
        }
        else {
            $('.highwire-controls').fadeOut(100);
        }
    };

    var useCrossref = function() {
        return $('#id_use_crossref').is(':checked');
    };

    var updateCrossrefControls = function() {
        if (useCrossref()) {
            $('.crossref-controls').fadeIn(200);
        }
        else {
            $('.crossref-controls').fadeOut(100);
            $('#id_crossref_username').val('');
            $('#id_crossref_password').val('');
        }
    };

    var useScopusApiKeysFromPool = function() {
        return $('#id_use_scopus_api_keys_from_pool').is(':checked');
    };

    var updateScopusControls = function() {
        if (useScopusApiKeysFromPool()) {
            $('.scopus-controls').fadeOut(200);
        }
        else {
            $('.scopus-controls').fadeIn(100);
        }
    };

    var updateValidateCrossrefButton = function() {
        var username = $('#id_crossref_username').val();
        var password = $('#id_crossref_password').val();
        var button = $('.validate-crossref-button');
        var message = $('.crossref-error-message');
        var checkmark = $('.validate-crossref-checkmark');
        var row = $('.crossref-form-row');

        message.hide();
        checkmark.hide();
        row.removeClass('error');

        if (username || password) {
            button.show();
        }
        else {
            button.hide();
        }
    };

    var checkCrossref = function() {
        var button = $('.validate-crossref-button');
        var loading = $('.validate-crossref-loading');

        button.hide();
        loading.show();

        var username = $('#id_crossref_username');
        var password = $('#id_crossref_password');
        var row = $('.crossref-form-row');
        var message = $('.crossref-error-message');
        var checkmark = $('.validate-crossref-checkmark');

        var data = [
            {name: 'username', value: username.val()},
            {name: 'password', value: password.val()},
        ];

        $.get(validateCrossrefUrl, data)
            .done(function(html) {
                loading.hide();
                if (html == 'ok') {
                    row.removeClass('error');
                    button.hide();
                    message.hide();
                    button.hide();
                    checkmark.show();
                }
                else {
                    row.addClass('error');
                    message.show();
                    button.show();
                    checkmark.hide();
                    button.addClass('disabled').show();
                }
                checkForm();
            });

        return false;
    };

    var isIssnRowEmpty = function(row) {
        var index = row.attr('index');
        var electronicIssn = row.find('#id_electronic_issn_' + index).val();
        var printIssn = row.find('#id_print_issn_' + index).val();
        var journalCode = row.find('#id_journal_code_' + index).val();
        return !electronicIssn && !printIssn && !journalCode;
    };

    var wireUpValidateIssnButton = function(rowSelector, index, cohort) {
        var row = $(rowSelector);
        var button = row.find('.validate-issn-button');

        button.on('click', function() {
            var usingJournal = hasHighWire() && !cohort;
            var loading = row.find('.validate-issn-loading');
            var checkmark = row.find('.validate-issn-checkmark');
            var message = row.find('.issn-error-message');

            button.hide();
            loading.show();

            var electronicIssn = row.find('#id_electronic_issn_' + index).val();
            var printIssn = row.find('#id_print_issn_' + index).val();

            if (usingJournal) {
                var journalCode = row.find('#id_journal_code_' + index).val();
            }

            var setIssnError = function(error) {
                row.addClass('error');
                message.html('<li>' + error + '</li>').show();
                button.show();
                checkmark.hide();
                button.addClass('disabled').show();
            };

            var setIssnWarning = function(warning) {
                message.html('<li>' + warning + '</li>').show();
                checkmark.show();
            };

            // quick local checks for blank entries
            if (electronicIssn == '' || printIssn == '' || (usingJournal && journalCode == '')) {
                loading.hide();
                setIssnError('All ISSN fields need a value.');
                return false;
            }

            var data = [
                {name: 'electronic_issn', value: electronicIssn},
                {name: 'print_issn', value: printIssn},
                {name: 'csrfmiddlewaretoken', value: csrfToken}
            ];

            if (usingJournal) {
                data.push(
                    {name: 'journal_code', value: journalCode}
                );
            }

            $.getJSON(validateIssnUrl, data)
                .done(function(json) {
                    loading.hide();
                    if (json.status == 'ok') {
                        row.removeClass('error');
                        button.hide();
                        message.hide();
                        button.hide();
                        checkmark.show();
                    }
                    else if (json.status == 'error') {
                        setIssnError(json.error_message);
                    }
                    else if (json.status == 'warning') {
                        row.removeClass('error');
                        setIssnWarning(json.warning_message);
                    }
                    checkForm();
                });

            return false;
        });
    };

    var wireUpIssnControls = function(rowSelector, index, cohort) {
        var row = $(rowSelector);
        row.find('input').on('keyup', function() {
            row.find('.validate-issn-checkmark').hide();
            row.find('.validate-issn-button').show();
        });

        if (!cohort) {
            $('#id_hw_addl_metadata_available').on('change', function () {
                if (hasHighWire()) {
                    row.find('.validate-issn-checkmark').hide();
                    row.find('.validate-issn-button').show();
                }
            });
        }
    };

    var wireUpDeleteIssnButton = function(rowSelector, index, cohort) {
        var row = $(rowSelector);
        row.find('.delete-issn-button').on('click', function() {
            row.remove();
            checkForm();
            return false;
        });
    };

    var showBuildingReportsModal = function() {
        $('#creating-publisher-modal').modal({
            backdrop: 'static',
            keyboard: false
        });

        setInterval(function() {
            $.getJSON(buildingPollUrl)
                .done(function(json) {
                    if (json.status == 'completed') {
                        window.location = buildingSuccessUrl;
                    }
                    else if (json.status == 'error') {
                        window.location = buildingErrorUrl;
                    }
                });
        }, 1000);
    };

    var submit = function() {
        var issnValues = [];
        $('.issn-values-row').each(function() {
            var row = $(this);
            if (!isIssnRowEmpty(row)) {
                var index = row.attr('index');
                issnValues.push({
                    electronic_issn: row.find('#id_electronic_issn_' + index).val(),
                    print_issn: row.find('#id_print_issn_' + index).val(),
                    journal_code: row.find('#id_journal_code_' + index).val(),
                    index: index
                });
            }
        });
        $('#id_issn_values').val(JSON.stringify(issnValues));

        var issnCohortValues = [];
        $('.issn-values-cohort-row').each(function() {
            var row = $(this);
            if (!isIssnRowEmpty(row)) {
                var index = row.attr('index');
                issnCohortValues.push({
                    electronic_issn: row.find('#id_electronic_issn_' + index).val(),
                    print_issn: row.find('#id_print_issn_' + index).val(),
                    index: index
                });
            }
        });
        $('#id_issn_values_cohort').val(JSON.stringify(issnCohortValues));

        var f = $('#hidden-publisher-form');
        f.find('input[name="publisher_id"]').val($('#id_publisher_id').val());
        f.find('input[name="name"]').val($('#id_name').val());
        f.find('input[name="issn_values"]').val($('#id_issn_values').val());
        f.find('input[name="use_scopus_api_keys_from_pool"]').val($('#id_use_scopus_api_keys_from_pool').is(':checked') ? 'on' : '');
        f.find('input[name="scopus_api_keys"]').val($('#id_scopus_api_keys').val());
        f.find('input[name="email"]').val($('#id_email').val());
        f.find('input[name="use_crossref"]').val($('#id_use_crossref').is(':checked') ? 'on' : '');
        f.find('input[name="crossref_username"]').val($('#id_crossref_username').val());
        f.find('input[name="crossref_password"]').val($('#id_crossref_password').val());
        f.find('input[name="hw_addl_metadata_available"]').val($('#id_hw_addl_metadata_available').is(':checked') ? 'on' : '');
        f.find('input[name="pilot"]').val($('#id_pilot').is(':checked') ? 'on' : '');
        f.find('input[name="published_articles"]').val($('#id_published_articles').is(':checked') ? 'on' : '');
        f.find('input[name="rejected_manuscripts"]').val($('#id_rejected_manuscripts').is(':checked') ? 'on' : '');
        f.find('input[name="cohort_articles"]').val($('#id_cohort_articles').is(':checked') ? 'on' : '');
        f.find('input[name="issn_values_cohort"]').val($('#id_issn_values_cohort').val());
        f.find('input[name="reports_username"]').val($('#id_reports_username').val());
        f.find('input[name="reports_password"]').val($('#id_reports_password').val());
        f.find('input[name="reports_project"]').val($('#id_reports_project').val());
        f.find('input[name="demo_id"]').val($('#id_demo_id').val());
        f.find('input[name="start_date"]').val($('#id_start_date').val());
        f.find('input[name="demo_notes"]').val($('#id_demo_notes').val());

        f.submit();
    };

    var init = function(options) {
        options = $.extend({
            publisherId: '',
            validateCrossrefUrl: '',
            validateIssnUrl: '',
            addIssnValuesUrl: '',
            buildingPollUrl: '',
            buildingSuccessUrl: '',
            buildingErrorUrl: '',
            csrfToken: '',
            isDemo: false
        }, options);

        publisherId = options.publisherId;
        validateCrossrefUrl = options.validateCrossrefUrl;
        validateIssnUrl = options.validateIssnUrl;
        addIssnValuesUrl = options.addIssnValuesUrl;
        buildingPollUrl = options.buildingPollUrl;
        buildingSuccessUrl = options.buildingSuccessUrl;
        buildingErrorUrl = options.buildingErrorUrl;
        csrfToken = options.csrfToken;
        isDemo = options.isDemo;

        isNew = publisherId == '';

        $('#id_publisher_id, #id_name, #id_email').on('keyup', checkForm);
        $('#id_reports_username, #id_reports_password, #id_reports_project').on('keyup', checkForm);
        $('#id_pilot').on('change', checkForm);

        if (isNew) {
            $('#id_reports_password').show();
        }
        $('.set-reports-password-link a').click(function() {
            $('.set-reports-password-link').hide();
            $('#id_reports_password').show().focus();
            return false;
        });

        $('#id_published_articles').on('change', function() {
            updatePublishedArticlesControls();
            checkForm();
        });
        updatePublishedArticlesControls();

        $('#id_rejected_manuscripts').on('change', function() {
            updateRejectedManuscriptsControls();
            checkForm();
        });
        updateRejectedManuscriptsControls();

        $('#id_cohort_articles').on('change', function() {
            updateCohortArticlesControls();
            checkForm();
        });
        updateCohortArticlesControls();

        $('#id_hw_addl_metadata_available').on('change', function() {
            updateHighWireControls();
            checkForm();
        });
        updateHighWireControls();

        $('#id_use_crossref').on('change', function() {
            updateCrossrefControls();
            checkForm();
        });
        updateCrossrefControls();

        if (isNew) {
            $('#id_use_scopus_api_keys_from_pool').on('change', function() {
                updateScopusControls();
                checkForm();
            });
            updateScopusControls();
        }

        $('#id_crossref_username, #id_crossref_password').on('keyup', function() {
            updateValidateCrossrefButton();
            checkForm();
        });
        $('.validate-crossref-button').on('click', checkCrossref);

        $('.add-issn-button').on('click', function() {
            $.get(addIssnValuesUrl)
                .done(function(html) {
                    $('#issn-values-container').append(html);
                    updateHighWireControls();
                    checkForm();
                });
            return false;
        });

        $('.add-issn-cohort-button').on('click', function() {
            $.get(addIssnValuesUrl, [{name: 'cohort', value: 1}])
                .done(function(html) {
                    $('#issn-values-cohort-container').append(html);
                    checkForm();
                });
            return false;
        });

        $('.submit-button.save-button').on('click', function(event) {
            submit();
            event.preventDefault();
            return false;
        });

        checkForm();
    };

    return {
        wireUpValidateIssnButton: wireUpValidateIssnButton,
        wireUpDeleteIssnButton: wireUpDeleteIssnButton,
        wireUpIssnControls: wireUpIssnControls,
        showBuildingReportsModal: showBuildingReportsModal,
        init: init
    };

})();


//
// Edit User page
//

var EditUserPage = (function() {
    var f;
    var email = '';

    var checkForm = function() {
        var email = $("#id_email").val();

        if (email) {
            f.find('.submit-button').removeClass('disabled').prop('disabled', false);
        }
        else {
            f.find('.submit-button').addClass('disabled').prop('disabled', true);
        }
    };

    var init = function(options) {
        options = $.extend({
            email: ''
        }, options);

        email = options.email;

        f = $('#user-form');
        f.find('#id_email').on('keyup', checkForm);

        f.find('.set-password-link a').click(function() {
            $('.set-password-link').hide();
            $('#id_password').show().focus();
        });

        f.find('#id_superuser').on('change', function() {
            if ($(this).is(':checked')) {
                f.find('#id_staff').prop("checked", true);
            }
        });

        f.find('#id_staff').on('change', function() {
            if (!$(this).is(':checked')) {
                f.find('#id_superuser').prop("checked", false);
            }
        });
    };

    return {
        init: init
    };

})();


//
// Growth page
//

var GrowthPage = (function() {
    var chartData;

    var addGrowth2 = function() {
        var data = growthData2();
        chartData.datum(data);
        nv.utils.windowResize(chart.update);
    };

    var showGraph = function(data) {
        var chart;
        var data;

        $('#chart').empty();

        nv.addGraph(function() {
            chart = nv.models.lineChart().options({
                height: 240,
                margin: {top: 30, right: 10, bottom: 40, left: 0},
                showYAxis: false,
                showLegend: false,
                transitionDuration: 300,
                useInteractiveGuideline: false
            });

            chart.xAxis.options({
                tickPadding: 15,
                tickValues: [
                    new Date(2014, 9, 1),
                    new Date(2015, 0, 1),
                    new Date(2015, 3, 1),
                    new Date(2015, 6, 1),
                    new Date(2015, 9, 1)
                ],
                tickFormat: function(d) {
                    return (d3.time.format('%b %Y'))(new Date(d));
                },
                showMaxMin: false
            });

            chartData = d3.select('#chart')
                .append('svg')
                .datum(data);

            chartData.call(chart);

            nv.utils.windowResize(chart.update);

            return chart;
        });
    };

    var showJournalsGraph = function() {
        $('.stats-ribbon .selectable').removeClass('active');
        $('#summary-graph-journals').addClass('active');
        $('.chart-title').html('Journals <span class="subtitle">Journals added over time</span>');
        showGraph(growthData1());
    };

    var showArticlesGraph = function() {
        $('.stats-ribbon .selectable').removeClass('active');
        $('#summary-graph-articles').addClass('active');
        $('.chart-title').html('Articles <span class="subtitle">Articles found over time</span>');
        showGraph(growthData2());
    };

    var showCitationsGraph = function() {
        $('.stats-ribbon .selectable').removeClass('active');
        $('#summary-graph-citations').addClass('active');
        $('.chart-title').html('Citations <span class="subtitle">Citations found over time</span>');
        showGraph(growthData3());
    };

    var init = function() {
        $('#summary-graph-journals').click(showJournalsGraph).click();
        $('#summary-graph-articles').click(showArticlesGraph);
        $('#summary-graph-citations').click(showCitationsGraph);
    };

    var growthData1 = function() {
        return [
            {
                area: true,
                values: [
                    {x: new Date(2014, 7, 1), y: 2},
                    {x: new Date(2014, 8, 1), y: 2},
                    {x: new Date(2014, 9, 1), y: 2},
                    {x: new Date(2014, 10, 1), y: 2},
                    {x: new Date(2014, 11, 1), y: 4},
                    {x: new Date(2015, 0, 1), y: 7},
                    {x: new Date(2015, 1, 1), y: 7},
                    {x: new Date(2015, 2, 1), y: 12},
                    {x: new Date(2015, 3, 1), y: 13},
                    {x: new Date(2015, 4, 1), y: 13},
                    {x: new Date(2015, 5, 1), y: 23},
                    {x: new Date(2015, 6, 1), y: 29},
                    {x: new Date(2015, 7, 1), y: 43},
                    {x: new Date(2015, 8, 1), y: 53},
                    {x: new Date(2015, 9, 1), y: 55},
                    {x: new Date(2015, 10, 1), y: 74},
                    {x: new Date(2015, 11, 1), y: 85}
                ],
                key: "Journals",
                color: "#0084ae",
                strokeWidth: 1,
                fillOpacity: .1
            }
        ];
    };

    var growthData2 = function() {
        return [
            {
                area: true,
                values: [
                    {x: new Date(2014, 7, 1), y: 2000},
                    {x: new Date(2014, 8, 1), y: 2100},
                    {x: new Date(2014, 9, 1), y: 2231},
                    {x: new Date(2014, 10, 1), y: 2632},
                    {x: new Date(2014, 11, 1), y: 4744},
                    {x: new Date(2015, 0, 1), y: 4997},
                    {x: new Date(2015, 1, 1), y: 5073},
                    {x: new Date(2015, 2, 1), y: 5200},
                    {x: new Date(2015, 3, 1), y: 5900},
                    {x: new Date(2015, 4, 1), y: 5953},
                    {x: new Date(2015, 5, 1), y: 15989},
                    {x: new Date(2015, 6, 1), y: 16922},
                    {x: new Date(2015, 7, 1), y: 33788},
                    {x: new Date(2015, 8, 1), y: 53665},
                    {x: new Date(2015, 9, 1), y: 55553},
                    {x: new Date(2015, 10, 1), y: 102333},
                    {x: new Date(2015, 11, 1), y: 134111}
                ],
                key: "Articles",
                color: "#009B81",
                strokeWidth: 1,
                fillOpacity: .1
            }
        ];
    };

    var growthData3 = function() {
        return [
            {
                area: true,
                values: [
                    {x: new Date(2014, 7, 1), y:   542000},
                    {x: new Date(2014, 8, 1), y:   552100},
                    {x: new Date(2014, 9, 1), y:   852231},
                    {x: new Date(2014, 10, 1), y:  902632},
                    {x: new Date(2014, 11, 1), y: 1114744},
                    {x: new Date(2015, 0, 1), y:  1284997},
                    {x: new Date(2015, 1, 1), y:  1335073},
                    {x: new Date(2015, 2, 1), y:  1799200},
                    {x: new Date(2015, 3, 1), y:  1805900},
                    {x: new Date(2015, 4, 1), y:  1905953},
                    {x: new Date(2015, 5, 1), y:  1915989},
                    {x: new Date(2015, 6, 1), y:  1916922},
                    {x: new Date(2015, 7, 1), y:  1953788},
                    {x: new Date(2015, 8, 1), y:  2013665},
                    {x: new Date(2015, 9, 1), y:  2025553},
                    {x: new Date(2015, 10, 1), y: 2002333},
                    {x: new Date(2015, 11, 1), y: 2124111}
                ],
                key: "Citations",
                color: "#FF6E00",
                strokeWidth: 1,
                fillOpacity: .1
            }
        ];
    };

    return {
        showJournalsGraph: showJournalsGraph,
        showArticlesGraph: showArticlesGraph,
        showCitationsGraph: showCitationsGraph,
        addGrowth2: addGrowth2,
        init: init
    };

})();


//
// Login page
//

var LoginPage = (function() {

    var checkForm = function() {
        var username = $('#id_email').val();
        var password = $('#id_password').val();
        if (username && password) {
            $('#login-button').removeClass('disabled btn-default').addClass('btn-primary').prop('disabled', false);
        }
        else {
            $('#login-button').addClass('disabled btn-default').removeClass('btn-primary').prop('disabled', true);
        }
    };

    var init = function() {
        $('#id_email').on('keyup', checkForm);
        $('#id_password').on('keyup', checkForm);

        $('#login-button').click(function () {
            $(this).fadeOut(100, function() {
                $('#login-loading').fadeIn(100);
            });
        });

        $('#id_email').focus();
    };

    return {
        init: init
    };

})();


//
// User Settings page
//

var UserSettingsPage = (function() {

    var init = function() {
        $('.set-password-link a').click(function() {
            $('.set-password-link').hide();
            $('#id_password').show().focus();
        });
    };

    return {
        init: init
    };

})();


//
// All pipelines page
//

var AllPipelinesPage = (function() {

    var init = function() {
    };

    return {
        init: init
    };

})();
