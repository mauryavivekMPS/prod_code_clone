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
