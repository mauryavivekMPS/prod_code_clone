//
// Common app functions
//

var IvetlWeb = (function() {
    var pjaxContainer = '#main-pjax-container';
    var initialPageUrl = '';
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

    var initPjax = function() {
        $(document).pjax('a:not(.no-default-pjax)', pjaxContainer).on('pjax:beforeSend', function (event, xhr) {
            // set an inception header for links with the right class
            if (event.relatedTarget && event.relatedTarget.className.indexOf('pjax-inception') != -1) {
                xhr.setRequestHeader('X-PJAX-INCEPTION', 'true');
            }
        });

        // get rid of any messages
        $(document).on('pjax:end', function () {
            hideMessages(true);
        });
    };

    var initPjaxSpinner = function() {
        $(document).on('pjax:send', function () {
            showLoading();
        });

        $(document).on('pjax:end', function () {
            hideLoading();
        });

        $(document).on('pjax:timeout', function(event) {
            // prevent default timeout redirection behavior
            event.preventDefault();
        });
    };

    var initTooltips = function() {
        $('[data-toggle="tooltip"]').tooltip();
        $(document).on('pjax:end', function () {
            $('[data-toggle="tooltip"]').tooltip();
        });
    };

    var setPageClasses = function(htmlClass, bodyClass) {
        $('html').removeClass().addClass(htmlClass);
        $('body').removeClass().addClass('meerkat ' + bodyClass);
    };

    var setInitialPageClasses = function(htmlClass, bodyClass) {
        initialPageUrl = window.location.href;
        $(document).on('pjax:end', function() {
            if (window.location.href == initialPageUrl) {
                setPageClasses(htmlClass, bodyClass);
            }
        });
    };

    var showMessages = function(messages, autoHide) {
        $('.messages-container').empty().html(messages).fadeIn(400);
        if (autoHide) {
            setTimeout(function() {
                hideMessages();
            }, 7000);
        }
    };

    var hideMessages = function(immediate) {
        if (immediate) {
            $('.messages-container').hide();
        }
        else {
            $('.messages-container').fadeOut(400);
        }
    };

    var showErrors = function(errors, autoHide) {
        $('.errors-container').empty().html(errors).fadeIn(400);
        if (autoHide) {
            setTimeout(function() {
                hideErrors();
            }, 7000);
        }
    };

    var hideErrors = function(immediate) {
        if (immediate) {
            $('.errors-container').hide();
        }
        else {
            $('.errors-container').fadeOut(400);
        }
    };

    return {
        pjaxContainer: pjaxContainer,
        showLoading: showLoading,
        hideLoading: hideLoading,
        initPjax: initPjax,
        initPjaxSpinner: initPjaxSpinner,
        initTooltips: initTooltips,
        setPageClasses: setPageClasses,
        setInitialPageClasses: setInitialPageClasses,
        showMessages: showMessages,
        hideMessages: hideMessages,
        showErrors: showErrors,
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

        $.get(updatePublisherUrl, data)
            .done(function(html) {
                if (html != 'No updates') {
                    $('.' + publisherId + '_row').remove();
                    summaryRow.replaceWith(html);
                    wirePublisherLinks('.' + publisherId + '_summary_row .publisher-link');
                    wireRunForPublisherForms('.' + publisherId + '_summary_row .run-pipeline-for-publisher-inline-form');
                    wireTaskLinks('.' + publisherId + '_row .task-link');

                    // store this publisher status and update the main run button
                    var newSummaryRow = $('.' + publisherId + '_summary_row');
                    publisherTaskStatus[publisherId] = newSummaryRow.attr('current_task_status');
                    updateRunButton();
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
            form.find('.run-pipeline-for-publisher-button').fadeOut(200);
            $('.run-button').fadeOut(200);
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
            f.find('.submit-button').removeClass('disabled');
        }
        else {
            f.find('.submit-button').addClass('disabled');
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
            f.find('.submit-button').removeClass('disabled');
        }
        else {
            f.find('.submit-button').addClass('disabled');
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
    var validateCrossrefUrl;
    var validateIssnUrl;
    var addIssnValuesUrl;
    var csrfToken;

    var checkForm = function() {
        var publisherId = f.find("#id_publisher_id").val();
        var name = f.find("#id_name").val();
        var publishedArticlesProduct = f.find('#id_published_articles').is(':checked');
        var rejectedArticlesProduct = f.find('#id_rejected_articles').is(':checked');

        if (publisherId && name && (publishedArticlesProduct || rejectedArticlesProduct)) {
            f.find('.submit-button').removeClass('disabled');
        }
        else {
            f.find('.submit-button').addClass('disabled');
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

    var updateCrossrefControls = function() {
        if ($('#id_use_crossref').is(':checked')) {
            $('.crossref-controls').fadeIn(200);
        }
        else {
            $('.crossref-controls').fadeOut(100);
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

    var wireUpValidateIssnButton = function(rowSelector, index, cohort) {
        var row = $(rowSelector);
        var button = row.find('.validate-issn-button');

        button.on('click', function() {
            var loading = row.find('.validate-issn-loading');
            var checkmark = row.find('.validate-issn-checkmark');
            var message = row.find('.issn-error-message');

            button.hide();
            loading.show();

            var data = [
                {name: 'electronic_issn', value: row.find('#id_electronic_issn_' + index).val()},
                {name: 'print_issn', value: f.find('#id_print_issn_' + index).val()},
                {name: 'csrfmiddlewaretoken', value: csrfToken}
            ];

            if (hasHighWire()) {
                data.push(
                    {name: 'journal_code', value: f.find('#id_journal_code_' + index).val()}
                );
            }

            $.get(validateIssnUrl, data)
                .done(function(response) {
                    loading.hide();
                    if (response == 'ok') {
                        row.removeClass('error');
                        button.hide();
                        message.hide();
                        button.hide();
                        checkmark.show();
                    }
                    else {
                        row.addClass('error');
                        message.html('<li>' + response + '</li>').show();  // smuggle the janky error message in through the response
                        button.show();
                        checkmark.hide();
                        button.addClass('disabled').show();
                    }
                });

            return false;
        });
    };

    var wireUpIssnControls = function(rowSelector, index, cohort) {
        console.log('wiring up for ' + rowSelector);
        var row = $(rowSelector);
        row.find('input').on('keyup', function() {
            row.find('.validate-issn-checkmark').hide();
            row.find('.validate-issn-button').show();
        });

        if (!cohort) {
            console.log('not a cohort');
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

        f = $('#publisher-form');
        f.find('#id_publisher_id').on('keyup', checkForm);
        f.find('#id_name').on('keyup', checkForm);

        $('#id_published_articles').on('change', function() {
            updatePublishedArticlesControls();
            checkForm();
        });
        updatePublishedArticlesControls();

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

        $('#id_use_crossref').on('change', updateCrossrefControls);
        updateCrossrefControls();

        f.find('#id_crossref_username').on('keyup', updateValidateCrossrefButton);
        f.find('#id_crossref_password').on('keyup', updateValidateCrossrefButton);
        f.find('.validate-crossref-button').on('click', checkCrossref);

        f.find('.add-issn-button').on('click', function() {
            $.get(addIssnValuesUrl)
                .done(function(html) {
                    $('#issn-values-container').append(html);
                    updateHighWireControls();
                });
            return false;
        });

        f.find('.add-issn-cohort-button').on('click', function() {
            $.get(addIssnValuesUrl, [{name: 'cohort', value: 1}])
                .done(function(html) {
                    $('#issn-values-cohort-container').append(html);
                });
            return false;
        });

        f.submit(function() {
            var issnValues = [];
            $('.issn-values-row').each(function() {
                var row = $(this);
                var index = row.attr('index');
                issnValues.push({
                    electronic_issn: row.find('#id_electronic_issn_' + index).val(),
                    print_issn: row.find('#id_print_issn_' + index).val(),
                    journal_code: row.find('#id_journal_code_' + index).val(),
                    index: index
                });
            });
            $('#id_issn_values').val(JSON.stringify(issnValues));

            var issnCohortValues = [];
            $('.issn-values-cohort-row').each(function() {
                var row = $(this);
                var index = row.attr('index');
                issnCohortValues.push({
                    electronic_issn: row.find('#id_electronic_issn_' + index).val(),
                    print_issn: row.find('#id_print_issn_' + index).val(),
                    index: index
                });
            });
            $('#id_issn_values_cohort').val(JSON.stringify(issnCohortValues));
        });
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
            f.find('.submit-button').removeClass('disabled');
        }
        else {
            f.find('.submit-button').addClass('disabled');
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
            $('#id_password').show();
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
            $('#id_password').show();
        });
    };

    return {
        init: init
    };

})();
