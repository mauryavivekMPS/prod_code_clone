$.widget("custom.loginpage", {
    
    _create: function() {
        $('#id_email').on('keyup change', this._checkForm).focus();
        $('#id_password').on('keyup change', this._checkForm);

        $('#login-button').click(function () {
            $(this).fadeOut(100, function() {
                $('#login-loading').fadeIn(100);
            });
        });
        this._checkForm();
    },

    _checkForm: function() {
        var username = $('#id_email').val();
        var password = $('#id_password').val();
        if (username && password) {
            $('#login-button').removeClass('disabled btn-default').addClass('btn-primary').prop('disabled', false);
        }
        else {
            $('#login-button').addClass('disabled btn-default').removeClass('btn-primary').prop('disabled', true);
        }
    }
});
