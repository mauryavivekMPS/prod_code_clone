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
