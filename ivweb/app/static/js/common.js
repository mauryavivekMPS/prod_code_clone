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
    var refreshIntervalIds = {};

    var updatePublisher = function(publisherId) {
        console.log('updating ' + publisherId);
        var summaryRow = $('.' + publisherId + '_summary_row');

        var data = [
            {name: 'csrfmiddlewaretoken', value: csrfToken},
            {name: 'publisher_id', value: publisherId},
            {name: 'current_job_id', value: summaryRow.attr('current_job_id')},
            {name: 'current_task_id', value: summaryRow.attr('current_task_id')},
            {name: 'current_task_status', value: summaryRow.attr('current_task_status')}
        ];

        $.get(updatePublisherUrl, data)
            .done(function(html) {
                if (html != 'No updates') {
                    $('.' + publisherId + '_row').remove();
                    $('.' + publisherId + '_summary_row').replaceWith(html);
                    wirePublisherLinks('.' + publisherId + '_summary_row .publisher-link');
                    wireTaskLinks('.' + publisherId + '_row .task-link');
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
                            var output = tailRow.find('.tail-output');
                            output.scrollTop(output[0].scrollHeight);
                        });
                }
                return false;
            });
        });
    };

    var init = function(options) {
        options = $.extend({
            pipelineId: '',
            publishers: [],
            tailUrl: '',
            updatePublisherUrl: '',
            csrfToken: ''
        }, options);

        pipelineId = options.pipelineId;
        csrfToken = options.csrfToken;
        updatePublisherUrl = options.updatePublisherUrl;
        tailUrl = options.tailUrl;

        $('.run-button').click(function() {
            $('#run-pipeline-form').submit();
            return false;
        });

        wirePublisherLinks('.publisher-link');
        wireTaskLinks('.task-link');

        $.each(options.publishers, function(index, publisherId) {
            setTimeout(function() {
                updatePublisher(publisherId);
            }, 3000);
        });

        $('.auto-refresh').each(function() {
            var link = $(this);
            link.click(function() {
                var publisherId = link.attr('publisher_id');
                var jobId = link.attr('job_id');
                var taskId = link.attr('task_id');
                var key = publisherId + '_' + jobId + '_' + taskId
                var tailRow = $('.' + key + '_row');
                var output = tailRow.find('.tail-output');
                var state = link.find('.auto-refresh-state');

                if (state.text() == 'OFF') {
                    state.text('ON').addClass('live');
                    output.addClass('live');
                    var pre = output.find('pre');
                    var autoRefreshInterval = setInterval(function() {

                        var existingLog = pre.text().trimRight();
                        var lastLine = '';
                        if (existingLog != '') {
                            lastLine = existingLog.slice(existingLog.lastIndexOf('\n') + 1);
                        }

                        var data = [
                            {name: 'csrfmiddlewaretoken', value: options.csrfToken},
                            {name: 'publisher_id', value: publisherId},
                            {name: 'job_id', value: jobId},
                            {name: 'task_id', value: taskId},
                            {name: 'last_line', value: lastLine}
                        ];

                        $.get(options.tailUrl, data)
                            .done(function(text) {
                                pre.append(text);
                            })
                            .always(function() {
                                output.scrollTop(output[0].scrollHeight);
                            });

                    }, 1000);
                    refreshIntervalIds[key] = autoRefreshInterval;
                }
                else {
                    clearInterval(refreshIntervalIds[key]);
                    state.text('OFF').removeClass('live');
                    output.removeClass('live');
                }
            })
        });
    };

    return {
        init: init
    };

})();


//
// Upload page
//

var UploadPage = (function() {
    var f;
    var pipelineId = '';

    var checkForm = function() {
        var publisherId = f.find("#id_publisher option:selected").val();
        var file = f.find("#id_file").val();

        if (publisherId && file) {
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

        f = $('#upload-form');
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