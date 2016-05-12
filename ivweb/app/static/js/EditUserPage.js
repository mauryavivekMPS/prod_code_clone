var EditUserPage = (function() {
    var f;
    var email = '';

    var checkForm = function() {
        var email = $("#id_email").val();

        if (email) {
            f.find('.submit-button').removeClass('disabled').prop('disabled', false);
        }
        else {
            f.find('.submit-button').addClass('disabled').prop('disabled', true);
        }
    };

    var init = function(options) {
        options = $.extend({
            email: ''
        }, options);

        email = options.email;

        f = $('#user-form');
        f.find('#id_email').on('keyup', checkForm);

        f.find('.set-password-link a').click(function() {
            $('.set-password-link').hide();
            $('#id_password').show().focus();
        });

        f.find('#id_superuser').on('change', function() {
            if ($(this).is(':checked')) {
                f.find('#id_staff').prop("checked", true);
            }
        });

        f.find('#id_staff').on('change', function() {
            if (!$(this).is(':checked')) {
                f.find('#id_superuser').prop("checked", false);
            }
        });
    };

    return {
        init: init
    };

})();
