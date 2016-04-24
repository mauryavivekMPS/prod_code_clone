var ListNotificationsPage = (function() {

    var init = function(options) {
        options = $.extend({
            notificationDetailsUrl: '',
            dismissNotificationUrl: '',
            csrfToken: ''
        }, options);

        $('.open-notification-details-link').click(function() {
            var notificationSummaryId = $(this).attr('notification_summary_id');
            var publisherId = $(this).attr('publisher_id');
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
                    });
            }


            return false;
        });
    };

    return {
        init: init
    };

})();
