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
// Dashboard page
//

var DashboardPage = (function() {

    var init = function() {
        // nothing yet
    };

    return {
        init: init
    };

})();
