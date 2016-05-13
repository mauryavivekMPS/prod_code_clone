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

    var initLeftNav = function(baseSelector) {
        $('.product-nav-item').click(function() {
            var productId = $(this).attr('product_id');
            var productMenu = $('.product-nav-menu-' + productId);
            if (productMenu.is(':visible')) {
                productMenu.hide();
                $.cookie('product-menu-' + productId, 'closed', {path: '/'});
            }
            else {
                productMenu.show();
                $.cookie('product-menu-' + productId, 'open', {path: '/'});
            }
            return false;
        });
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
        initLeftNav: initLeftNav,
        setPageClasses: setPageClasses,
        resetUrl: resetUrl,
        hideMessagesAfterDelay: hideMessagesAfterDelay,
        hideMessages: hideMessages,
        hideErrorsAfterDelay: hideErrorsAfterDelay,
        hideErrors: hideErrors
    };

})();
