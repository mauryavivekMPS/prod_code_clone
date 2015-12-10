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
        }, 5000);

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
            form.find('.run-pipeline-for-publisher-button').hide();
            form.find('.run-loading-icon').show();
            $('.run-button').hide();
            $.post(runForPublisherUrl, form.serialize());
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
            csrfToken: ''
        }, options);

        pipelineId = options.pipelineId;
        csrfToken = options.csrfToken;
        updatePublisherUrl = options.updatePublisherUrl;
        runForPublisherUrl = options.runForPublisherUrl;
        runForAllUrl = options.runForAllUrl;
        tailUrl = options.tailUrl;
        isSuperuser = options.isSuperuser;

        if (isSuperuser) {
            $('.run-button').click(function() {
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
        var file = f.find("#id_file").val();

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

        f.find('#id_file').on('change', checkForm);

        f.submit(function() {
            IvetlWeb.showLoading();
        });
    };

    return {
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
    var f;
    var publisherId;
    var isNew;
    var validateCrossrefUrl;
    var validateIssnUrl;
    var addIssnValuesUrl;
    var csrfToken;

    var checkForm = function() {
        var publisherId = f.find("#id_publisher_id").val();
        var name = f.find("#id_name").val();
        var email = f.find("#id_email").val();
        var hasBasics = publisherId != '' && name != '' && email != '';

        var publishedArticlesProduct = f.find('#id_published_articles').is(':checked');
        var rejectedManuscriptsProduct = f.find('#id_rejected_manuscripts').is(':checked');
        var cohortArticlesProduct = f.find('#id_cohort_articles').is(':checked');
        var atLeastOneProduct = publishedArticlesProduct || rejectedManuscriptsProduct || cohortArticlesProduct;

        var hasReportsDetails = true;
        if (isNew) {
            var reportsUsername = f.find('#id_reports_username').val();
            var reportsPassword = f.find('#id_reports_username').val();
            var reportsProject = f.find('#id_reports_project').val();
            hasReportsDetails = reportsUsername && reportsPassword && reportsProject;
        }

        var crossref = true;
        if (useCrossref()) {
            var username = f.find('#id_crossref_username').val();
            var password = f.find('#id_crossref_password').val();
            var validated = f.find('.validate-crossref-checkmark').is(':visible');
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
            $('.issn-values-cohort-row').each(function () {
                var row = $(this);
                if (!row.find('.validate-issn-checkmark').is(':visible')) {
                    validCohortIssns = false;
                    return false;
                }
            });
        }

        if (hasBasics && atLeastOneProduct && hasReportsDetails && crossref && validIssns && validCohortIssns) {
            f.find('.submit-button').removeClass('disabled').prop('disabled', false);
        }
        else {
            f.find('.submit-button').addClass('disabled').prop('disabled', true);
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
        var username = f.find('#id_crossref_username').val();
        var password = f.find('#id_crossref_password').val();
        var button = f.find('.validate-crossref-button');
        var message = f.find('.crossref-error-message');
        var checkmark = f.find('.validate-crossref-checkmark');
        var row = f.find('.crossref-form-row');

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
        var button = f.find('.validate-crossref-button');
        var loading = f.find('.validate-crossref-loading');

        button.hide();
        loading.show();

        var username = f.find('#id_crossref_username');
        var password = f.find('#id_crossref_password');
        var row = f.find('.crossref-form-row');
        var message = f.find('.crossref-error-message');
        var checkmark = f.find('.validate-crossref-checkmark');

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

    var updateValidateIssnButton = function() {
        var username = f.find('#id_crossref_username').val();
        var password = f.find('#id_crossref_password').val();
        var button = f.find('.validate-crossref-button');
        var message = f.find('.crossref-error-message');
        var checkmark = f.find('.validate-crossref-checkmark');
        var row = f.find('.crossref-form-row');

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

    var init = function(options) {
        options = $.extend({
            publisherId: '',
            validateCrossrefUrl: '',
            validateIssnUrl: '',
            addIssnValuesUrl: '',
            csrfToken: ''
        }, options);

        publisherId = options.publisherId;
        validateCrossrefUrl = options.validateCrossrefUrl;
        validateIssnUrl = options.validateIssnUrl;
        addIssnValuesUrl = options.addIssnValuesUrl;
        csrfToken = options.csrfToken;

        isNew = publisherId == '';

        f = $('#publisher-form');
        f.find('#id_publisher_id, #id_name, #id_email').on('keyup', checkForm);
        f.find('#id_reports_username, #id_reports_password, #id_reports_project').on('keyup', checkForm);
        $('#id_pilot').on('change', checkForm);

        $('#id_published_articles').on('change', function() {
            updatePublishedArticlesControls();
            checkForm();
        });
        updatePublishedArticlesControls();

        $('#id_rejected_manuscripts').on('change', checkForm);

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

        f.find('#id_crossref_username, #id_crossref_password').on('keyup', function() {
            updateValidateCrossrefButton();
            checkForm();
        });
        f.find('.validate-crossref-button').on('click', checkCrossref);

        f.find('.add-issn-button').on('click', function() {
            $.get(addIssnValuesUrl)
                .done(function(html) {
                    $('#issn-values-container').append(html);
                    updateHighWireControls();
                    checkForm();
                });
            return false;
        });

        f.find('.add-issn-cohort-button').on('click', function() {
            $.get(addIssnValuesUrl, [{name: 'cohort', value: 1}])
                .done(function(html) {
                    $('#issn-values-cohort-container').append(html);
                    checkForm();
                });
            return false;
        });

        f.submit(function() {
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
        });

        checkForm();
    };

    return {
        wireUpValidateIssnButton: wireUpValidateIssnButton,
        wireUpDeleteIssnButton: wireUpDeleteIssnButton,
        wireUpIssnControls: wireUpIssnControls,
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
        var email = f.find("#id_email").val();

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
    };

    return {
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
