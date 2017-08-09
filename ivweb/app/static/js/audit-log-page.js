$.widget("custom.auditlogpage", {

    _create: function () {
        var self = this;

        $('.filter-menu').on('change', function () {
            IvetlWeb.showLoading();
            self._applyFilter();
            self._updateFilterDisplay();
        });

        this._updateFilterDisplay();
    },

    _applyFilter: function () {
        var q = '?time=' + $('#id_time_filter').val();

        var publisher = $('#id_publisher_filter').val();
        var user = $('#id_user_filter').val();

        if (publisher) {
            window.location = q + '&publisher=' + publisher;
        }
        else if (user) {
            window.location = q + '&user=' + user;
        }
        else {
            window.location = q;
        }
    },

    _updateFilterDisplay: function () {
        var publisherMenu = $('#id_publisher_filter');
        var userMenu = $('#id_user_filter');

        if (publisherMenu.val()) {
            userMenu.addClass('disabled').attr('disabled', true);
        }
        else {
            userMenu.removeClass('disabled').attr('disabled', false);
        }

        if (userMenu.val()) {
            publisherMenu.addClass('disabled').attr('disabled', true);
        }
        else {
            publisherMenu.removeClass('disabled').attr('disabled', false);
        }
    }
});
