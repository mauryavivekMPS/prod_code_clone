var PendingFilesForm = (function() {
    var isDemo;

    var enableSubmitForProcessing = function() {
        $('.submit-for-processing-button').removeClass('disabled').prop('disabled', false);
    };

    var disableSubmitForProcessing = function() {
        $('.submit-for-processing-button').addClass('disabled').prop('disabled', true);
    };

    var updateSubmitForProcessing = function() {
        if (!isDemo) {
            var table = $('table.all-files-table');
            if (table.find('> tbody > tr.validated-file').length > 0) {
                enableSubmitForProcessing();
            }
            else {
                disableSubmitForProcessing();
            }
        }
    };

    var init = function(options) {
        options = $.extend({
            isDemo: false
        }, options);

        isDemo = options.isDemo;

        updateSubmitForProcessing();
    };

    return {
        updateSubmitForProcessing: updateSubmitForProcessing,
        init: init
    };

})();
