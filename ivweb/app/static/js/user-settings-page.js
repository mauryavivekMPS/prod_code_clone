$.widget("custom.usersettingspage", {

    _create: function () {
        var self = this;

        $('.set-password-link a').click(function () {
            $('.submit-button').addClass('disabled').prop('disabled', false);
            $('.set-password-link').hide();
            $('#id_password').show().focus();
            $('#id_password_confirm').show();
        });

        $('#id_password, #id_password_confirm').on('keyup', function () {
            self._checkForm();
        });
    },

    _checkForm: function () {
        var password = $('#id_password').val();
        var passwordErrorMessage = $('.password-error-message');
        if (password) {
            var passwordConfirm = $('#id_password_confirm').val();
            if (password !== passwordConfirm) {
                $('.submit-button').addClass('disabled').prop('disabled', false);
                passwordErrorMessage.show();
            }
            else {
                $('.submit-button').removeClass('disabled').prop('disabled', false);
                passwordErrorMessage.hide();
            }
        }
        else {
            $('.submit-button').removeClass('disabled').prop('disabled', false);
            passwordErrorMessage.hide();
        }
    }
});
