var ListDemosPage = (function() {

    var init = function(options) {
        options = $.extend({
            updateDemoStatusUrl: '',
            csrfToken: ''
        }, options);

        $('.inline-demo-status-menu').on('change', function () {
            var menu = $(this);
            var status = menu.find("option:selected").val();
            var statusName = menu.find("option:selected").text();
            var demoId = menu.attr('demo_id');
            var demoName = menu.attr('demo_name');
            var previousStatus = menu.attr('previous_status');

            // update the modal and open it
            var m = $('#set-email-message-modal');
            m.find('.status-change-details').html('<b>' + demoName + '</b> <span class="lnr lnr-arrow-right"></span> <b>' + statusName + '</b>');

            var submitButton = m.find('.set-email-message-submit-button');
            submitButton.on('click', function() {
                submitButton.off('click');
                m.off('hidden.bs.modal');
                m.modal('hide');

                IvetlWeb.showLoading();

                var data = [
                    {name: 'csrfmiddlewaretoken', value: options.csrfToken},
                    {name: 'demo_id', value: demoId},
                    {name: 'status', value: status},
                    {name: 'message', value: $('#id_custom_status_message').val()}
                ];

                $.post(options.updateDemoStatusUrl, data)
                    .always(function() {
                        IvetlWeb.hideLoading();
                    });

                menu.attr('previous_status', status);
            });

            var cancelButton = m.find('.set-email-message-cancel-button');
            cancelButton.on('click', function() {
                $(this).off('click');
                menu.val(previousStatus);
            });

            m.modal();

            m.on('hidden.bs.modal', function () {
                submitButton.off('click');
                m.off('hidden.bs.modal');
            });
        });
    };

    return {
        init: init
    };

})();
