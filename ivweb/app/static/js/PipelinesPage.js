var PipelinePage = (function() {
    var productId;
    var pipelineId;
    var csrfToken;
    var updatePublisherUrl;
    var tailUrl;
    var jobActionUrl;
    var runForPublisherUrl;
    var runForAllUrl;
    var isSuperuser;
    var tailIntervalIds = {};
    var publisherTaskStatus = {};
    var pipelineName;
    var singlePublisherPipeline;
    var includeDateRangeControls;
    var includeFromDateControls;
    var supportsRestart;

    var initialDelay = 3000;  // 3 seconds minimum
    var maxDelay = 384000;  // 6 minutes-ish max
    var delayIncreaseMultiple = 2;  // increase the delay by 2x each time

    var updateRunButton = function() {
        var somethingIsRunning = false;
        $.each(publisherTaskStatus, function(publisherId) {
            if (publisherTaskStatus[publisherId] === 'in-progress') {
                somethingIsRunning = true;
                return false;
            }
        });
        if (somethingIsRunning) {
            $('.run-button, .run-single-publisher-pipeline-button, .last-updated-message').hide();
        }
        else {
            $('.run-button, .run-single-publisher-pipeline-button, .last-updated-message').show();
        }
    };

    var updatePublisher = function(publisherId, currentDelay) {
        var summaryRow = $('.' + publisherId + '_summary_row');
        var opened = 0;
        var newDelay = currentDelay;
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
                    wireRestartRunButtons('.' + publisherId + '_restart-run-button');
                    wireJobActionsDropdown('.' + publisherId + '_job-actions-dropdown');
                    wireTaskLinks('.' + publisherId + '_row .task-link');
                    onUpdatePublisher(publisherId);
                }

                // update the progress bar
                if (json.has_progress_bar_updates) {
                    var progressBarContainer = $('.' + publisherId + '_row .task-progress');
                    var progressBar = progressBarContainer.find('.progress-bar');
                    var newTitle = 'Processing ' + json.current_record_count + ' of ' + json.total_record_count + ' records';
                    progressBarContainer.attr('data-original-title', newTitle).tooltip('show');
                    progressBar.css('width', json.percent_complete + '%');
                }

                // if nothing has changed, increase the delay before the next check (if it's not maxed out already)
                if (json.has_section_updates || json.has_progress_bar_updates) {
                    newDelay = initialDelay;
                }
                else {
                    if (currentDelay < maxDelay) {
                        newDelay *= delayIncreaseMultiple;
                    }
                }
            });

        // start again...
        setTimeout(function() {
            updatePublisher(publisherId, newDelay);
        }, newDelay);
    };

    var onUpdatePublisher = function(publisherId) {
        var newSummaryRow = $('.' + publisherId + '_summary_row');
        publisherTaskStatus[publisherId] = newSummaryRow.attr('current_task_status');
        updateRunButton();
    };

    var openPublisher = function (publisherId) {
        var openerIcon = $('.' + publisherId + '_opener');
        var closerIcon = $('.' + publisherId + '_closer');
        $('.' + publisherId + '_row:not(.tail-row)').fadeIn(200);
        $('.' + publisherId + '_summary_row .summary-value').fadeOut(100);
        closerIcon.hide();
        openerIcon.show();
    };

    var closePublisher = function (publisherId) {
        var openerIcon = $('.' + publisherId + '_opener');
        var closerIcon = $('.' + publisherId + '_closer');
        $('.' + publisherId + '_row').fadeOut(100);
        $('.' + publisherId + '_summary_row .summary-value').fadeIn(100);
        openerIcon.hide();
        closerIcon.show();
    };

    var wirePublisherLinks = function(selector) {
        $(selector).each(function() {
            var link = $(this);
            link.click(function() {
                var publisherId = link.attr('publisher_id');
                var openerIcon = $('.' + publisherId + '_opener');

                // use the icon to figure out if open or closed
                if (openerIcon.is(':visible')) {
                    closePublisher(publisherId);
                }
                else {
                    openPublisher(publisherId);
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
            var m = $('#confirm-run-one-modal');

            if (includeDateRangeControls || includeFromDateControls) {
                $('#id_run_one_modal_from_date').val(form.find('input[name="from_date"]').val());
            }
            if (includeDateRangeControls) {
                $('#id_run_one_modal_to_date').val(form.find('input[name="to_date"]').val());
            }

            if (supportsRestart && form.find('input[name="restart_job_id"]').val()) {
                m.find('.modal-title').html('Restart Job for Publisher');
                m.find('.modal-body .confirm-run-one-modal-content').html('<p>Are you sure you want to restart the ' + pipelineName + ' job for <span style="font-weight:600">' + publisherName + '</span>?</p>');
            }
            else {
                if (includeDateRangeControls) {
                    m.find('.modal-title').html('Run Pipeline for Publisher');
                    m.find('.modal-body .confirm-run-one-modal-content').html('<p>Run the ' + pipelineName + ' pipeline for <span style="font-weight:600">' + publisherName + '</span> for the following dates:</p>');
                }
                else if (includeFromDateControls) {
                    m.find('.modal-title').html('Run Pipeline for Publisher');
                    m.find('.modal-body .confirm-run-one-modal-content').html('<p>Run the ' + pipelineName + ' pipeline for <span style="font-weight:600">' + publisherName + '</span> starting at the following date:</p>');
                }
                else {
                    m.find('.modal-title').html('Run Pipeline for Publisher');
                    m.find('.modal-body .confirm-run-one-modal-content').html('<p>Are you sure you want to run the ' + pipelineName + ' pipeline for <span style="font-weight:600">' + publisherName + '</span>?</p>');
                }
            }

            var submitButton = m.find('.confirm-run-one-submit-button');
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

                if (includeDateRangeControls || includeFromDateControls) {
                    form.find('input[name="from_date"]').val($('#id_run_one_modal_from_date').val());
                }
                if (includeDateRangeControls) {
                    form.find('input[name="to_date"]').val($('#id_run_one_modal_to_date').val());
                }

                form.find('input[name="send_alerts"]').val(m.find('input[name="send_alerts"]').is(':checked') ? '1' : '');

                $.post(runForPublisherUrl, form.serialize());

                // clear out any job IDs, this form is used by multiple buttons (i.e. run and multiple restart)
                form.find('input[name="restart_job_id"]').val('');
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

    var wireRestartRunButtons = function(selector) {
        $(selector).each(function() {
            var button = $(this);
            var publisherId = button.attr('publisher_id');
            var jobId = button.attr('job_id');
            button.click(function() {
                var f = $('.' + publisherId + '_summary_row .run-pipeline-for-publisher-inline-form');
                var jobIdWidget = f.find('input[name="restart_job_id"]');
                jobIdWidget.val(jobId);
                f[0].submit();
                return false;
            });
        });
    };

    var wireJobActionsDropdown = function(selector) {
        $(selector).each(function () {
            var dropdown = $(this);
            var publisherId = dropdown.attr('publisher_id');
            var jobId = dropdown.attr('job_id');
            dropdown.find('.action-link').click(function (e) {
                var data = {
                    csrfmiddlewaretoken: csrfToken,
                    publisher_id: publisherId,
                    job_id: jobId,
                    action: $(this).attr('action')
                };
                $.post(jobActionUrl, data);
                e.preventDefault();
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
            productId: '',
            pipelineId: '',
            publishers: [],
            tailUrl: '',
            jobActionUrl: '',
            updatePublisherUrl: '',
            runForPublisherUrl: '',
            runForAllUrl: '',
            isSuperuser: false,
            csrfToken: '',
            pipelineName: '',
            singlePublisherPipeline: false,
            includeDateRangeControls: false,
            includeFromDateControls: false,
            supportsRestart: false
        }, options);

        productId = options.productId;
        pipelineId = options.pipelineId;
        csrfToken = options.csrfToken;
        updatePublisherUrl = options.updatePublisherUrl;
        runForPublisherUrl = options.runForPublisherUrl;
        runForAllUrl = options.runForAllUrl;
        tailUrl = options.tailUrl;
        jobActionUrl = options.jobActionUrl;
        isSuperuser = options.isSuperuser;
        pipelineName = options.pipelineName;
        singlePublisherPipeline = options.singlePublisherPipeline;
        includeDateRangeControls = options.includeDateRangeControls;
        includeFromDateControls = options.includeFromDateControls;

        if (isSuperuser) {
            if (singlePublisherPipeline) {
                if (includeDateRangeControls) {
                    $('#id_run_single_publisher_pipeline_modal_from_date').datepicker({
                        autoclose: true
                    });

                    $('#id_run_single_publisher_pipeline_modal_to_date').datepicker({
                        autoclose: true
                    });
                }

                var singlePublisherPipelineModal = $('#confirm-run-single-publisher-pipeline-modal');
                $('.run-single-publisher-pipeline-button').click(function() {
                    $('#id_run_single_publisher_pipeline_modal_from_date').val($('.run-pipeline-for-publisher-inline-form input[name="from_date"]').val());
                    $('#id_run_single_publisher_pipeline_modal_to_date').val($('.run-pipeline-for-publisher-inline-form input[name="to_date"]').val());
                    singlePublisherPipelineModal.modal();
                });

                var singleForm = $('#run-single-publisher-pipeline-form');
                var singleModal = $('#confirm-run-single-publisher-pipeline-modal');
                singleModal.find('.confirm-run-single-publisher-pipeline-submit-button').click(function() {
                    singlePublisherPipelineModal.modal('hide');
                    $('.run-single-publisher-pipeline-button, .last-updated-message').hide();
                    var loading = $('.run-single-publisher-pipeline-loading-icon');
                    loading.show();
                    setTimeout(function() {
                        loading.hide();
                    }, 3000);

                    if (includeDateRangeControls || includeFromDateControls) {
                        singleForm.find('input[name="from_date"]').val(singleModal.find('input[name="from_date"]').val());
                    }
                    if (includeDateRangeControls) {
                        singleForm.find('input[name="to_date"]').val(singleModal.find('input[name="to_date"]').val());
                    }

                    singleForm.find('input[name="send_alerts"]').val(singleModal.find('input[name="send_alerts"]').is(':checked') ? '1' : '');
                    singleForm.submit();
                    return false;
                });
            }
            else {
                if (includeDateRangeControls || includeFromDateControls) {
                    $('#id_run_one_modal_from_date').datepicker({
                        autoclose: true
                    });
                }
                if (includeDateRangeControls) {
                    $('#id_run_one_modal_to_date').datepicker({
                        autoclose: true
                    });

                    $('#id_run_all_modal_from_date').datepicker({
                        autoclose: true
                    });

                    $('#id_run_all_modal_to_date').datepicker({
                        autoclose: true
                    });
                }

                var allModal = $('#confirm-run-all-modal');
                var allForm = $('#run-pipeline-form');

                $('.run-button').click(function() {
                    allModal.modal();
                });

                allModal.find('.confirm-run-all-submit-button').click(function() {
                    allModal.modal('hide');
                    $('.run-button').hide();
                    var loading = $('.run-for-all-loading-icon');
                    loading.show();
                    setTimeout(function() {
                        loading.hide();
                    }, 3000);

                    if (includeDateRangeControls) {
                        allForm.find('input[name="from_date"]').val(allModal.find('input[name="from_date"]').val());
                        allForm.find('input[name="to_date"]').val(allModal.find('input[name="to_date"]').val());
                    }

                    allForm.find('input[name="send_alerts"]').val(allModal.find('input[name="send_alerts"]').is(':checked') ? '1' : '');
                    allForm.submit();
                    return false;
                });

                $('.monthly-message-link').on('click', function () {
                    $('.monthly-message-summary').hide();
                    $('.monthly-message-form').show();
                });

                $('.cancel-monthly-message').on('click', function () {
                    $('.monthly-message-form').hide();
                    $('.monthly-message-summary').show();
                });

                $('.save-monthly-message').on('click', function () {
                    console.log('here!');

                    $('.monthly-message-form').hide();
                    $('.monthly-message-summary').show();

                    var message = $('.monthly-message-textarea').val();
                    console.log('the message is: ');
                    console.log(message);

                    var data = [
                        {name: 'csrfmiddlewaretoken', value: csrfToken},
                        {name: 'product_id', value: productId},
                        {name: 'pipeline_id', value: pipelineId},
                        {name: 'message', value: message}
                    ];

                    $.post('/savemonthlymessage/', data)
                        .done(function () {
                            console.log('in done');

                            if (message) {
                                truncatedMessage = message.slice(0, 100);
                                if (message.length > 100) {
                                    truncatedMessage += '...';
                                }
                                $('.monthly-message-label').show();
                                $('.monthly-message-truncated-display').text(truncatedMessage);
                                $('.monthly-message-link-add').hide();
                                $('.monthly-message-link-edit').show();
                            }
                            else {
                                $('.monthly-message-label').hide();
                                $('.monthly-message-truncated-display').text('No monthly message');
                                $('.monthly-message-link-add').show();
                                $('.monthly-message-link-edit').hide();
                            }

                            $('.monthly-message-form').hide();
                            $('.monthly-message-summary').show();
                        })
                        .always(function () {
                            // nothing
                        });

                });
            }

            wirePublisherLinks('.publisher-link');
            wireTaskLinks('.task-link');
        }

        wireRunForPublisherForms('.run-pipeline-for-publisher-inline-form');
        wireRestartRunButtons('.restart-run-button');
        wireJobActionsDropdown('.job-actions-dropdown');

        $.each(options.publishers, function(index, publisherId) {
            setTimeout(function() {
                updatePublisher(publisherId, initialDelay);
            }, initialDelay);
        });

        var publisherId = window.location.hash.substr(1);
        if (publisherId) {
            openPublisher(publisherId);
        }
    };

    return {
        init: init,
        startTailForPublisher: startTailForPublisher,
        cancelTailForPublisher: cancelTailForPublisher,
        onUpdatePublisher: onUpdatePublisher
    };

})();
