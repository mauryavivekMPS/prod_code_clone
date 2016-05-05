var ListNotificationsPage = (function() {

    var init = function(options) {
        options = $.extend({
            notificationDetailsUrl: '',
            dismissNotificationUrl: '',
            openNotification: null,
            csrfToken: ''
        }, options);

        $('.open-notification-details-link').click(function() {
            var notificationSummaryId = $(this).attr('notification_summary_id');
            var publisherId = $(this).attr('publisher_id');
            var summaryRow = $('.notification-summary-' + notificationSummaryId);
            var detailsRow = $('.notification-details-' + notificationSummaryId);

            if (detailsRow.is(':visible')) {
                detailsRow.empty().fadeOut(100);
            }
            else {
                var data = [
                    {name: 'notification_summary_id', value: notificationSummaryId},
                    {name: 'publisher_id', value: publisherId}
                ];

                $.get(options.notificationDetailsUrl, data)
                    .done(function(html) {
                        detailsRow.empty().html(html).fadeIn(200);

                        detailsRow.find('.dismiss-notification-link').click(function() {
                            var data = [
                                {name: 'notification_summary_id', value: notificationSummaryId},
                                {name: 'publisher_id', value: publisherId},
                                {name: 'csrfmiddlewaretoken', value: options.csrfToken}
                            ];

                            $.post(options.dismissNotificationUrl, data)
                                .done(function() {
                                    summaryRow.fadeOut(100);
                                    detailsRow.fadeOut(100);
                                });

                            return false;
                        });
                    });
            }

            return false;
        });

        if (options.openNotification) {
            $('.notification-summary-' + options.openNotification + ' .open-notification-details-link').click();
        }
    };

    return {
        init: init
    };

})();
