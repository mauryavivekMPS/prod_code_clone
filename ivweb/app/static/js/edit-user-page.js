$.widget("custom.edituserpage", {

    _create: function () {
        var self = this;

        this.f = $('#user-form');
        this.f.find('#id_email').on('keyup', function () {
            self._checkForm();
        });

        this.f.find('.set-password-link a').click(function () {
            $('.set-password-link').hide();
            $('#id_password').show().focus();
        });

        this.f.find('#id_superuser').on('change', function () {
            if ($(this).is(':checked')) {
                self.f.find('#id_staff').prop("checked", true);
            }
        });

        this.f.find('#id_staff').on('change', function () {
            if (!$(this).is(':checked')) {
                self.f.find('#id_superuser').prop("checked", false);
            }
        });

        var publisherMultiselect = $('#publisher-multiselect');
        publisherMultiselect.multiselect({
            templates: {
                button: '<a href="#" class="multiselect dropdown-toggle form-control-static" data-toggle="dropdown">Add/remove publishers...</a>'
            },
            buttonClass: '',
            onChange: function (option, checked, select) {
                $('#id_publishers').val(publisherMultiselect.val().join(','));
            }
        });
    },

    _checkForm: function () {
        var email = $("#id_email").val();

        if (email) {
            this.f.find('.submit-button').removeClass('disabled').prop('disabled', false);
        }
        else {
            this.f.find('.submit-button').addClass('disabled').prop('disabled', true);
        }
    }
});
