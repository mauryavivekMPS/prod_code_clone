$.widget("custom.edituserpage", {
    options: {
        publisherNameById: {}
    },

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

        var publisherMultiselect = $('#publisher-multiselect');
        publisherMultiselect.multiselect({
            templates: {
                button: '<a href="#" class="multiselect dropdown-toggle form-control-static" data-toggle="dropdown">Add/remove publishers...</a>'
            },
            buttonClass: '',
            maxHeight: 338,
            onChange: function () {
                $('#id_publishers').val(publisherMultiselect.val().join(','));
                self._updateSelectedPublisherList();
            }
        });

        $('#id_user_type').on('change', function () {
            self._updatePublisherControls();
        });

        this._updateSelectedPublisherList();
        this._updatePublisherControls();
    },

    _updatePublisherControls: function () {
        if ($('#id_user_type').val() === 'hw-superuser') {
            $('.staff-selected').hide();
            $('.superuser-selected').show();
        }
        else {
            $('.superuser-selected').hide();
            $('.staff-selected').show();
        }
    },

    _updateSelectedPublisherList: function () {
        var self = this;
        var selectedPublishersListElement = $('.selected-publishers-list');
        selectedPublishersListElement.empty();

        var numSelectedPublishers = 0;
        var selectedPublishers = $('#publisher-multiselect').val();
        if (selectedPublishers) {
            numSelectedPublishers = selectedPublishers.length;
            $.each(selectedPublishers, function (index, publisher_id) {
                selectedPublishersListElement.append('<li>' + self.options.publisherNameById[publisher_id] + '</li>');
            });
        }
        var numberElement = $('.number-of-publishers-selected');
        if (numSelectedPublishers === 0) {
            numberElement.text('No publishers selected');
        }
        else if (numSelectedPublishers === 1) {
            numberElement.text('1 publisher selected');
        }
        else
        {
            numberElement.text(numSelectedPublishers + ' publishers selected');
        }
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
