$.widget("custom.auditlogpage", {

    _create: function () {
        var self = this;

        $('.filter-menu').on('change', function () {
            IvetlWeb.showLoading();
            self._applyFilter();
        });
    },

    _applyFilter: function () {
        var q = '?time=' + $('#id_time_filter').val();

        var publisher = $('#id_publisher_filter').val();
        var user = $('#id_user_filter').val();

        if (publisher) {
            q += '&publisher=' + publisher;
        }

        if (user) {
            q += '&user=' + user;
        }

        window.location = q;
    }
});
