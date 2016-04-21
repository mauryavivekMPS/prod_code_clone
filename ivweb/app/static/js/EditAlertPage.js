var EditAlertPage = (function() {
    var params;

    var checkForm = function() {
        var checkId = $("#id_check_id option:selected").val();
        var publisherId = $("#id_publisher_id option:selected").val();
        var name = $('#id_name').val()

        var gotParamValues = true;
        $.each(params, function(index, param) {
            if (!$('#id_param_' + param.name).val()) {
                gotParamValues = false;
            }
        });

        if (publisherId && checkId && name && gotParamValues) {
            $('.submit-button').removeClass('disabled').prop('disabled', false);
        }
        else {
            $('.submit-button').addClass('disabled').prop('disabled', false);
        }
    };


    var init = function(options) {
        options = $.extend({
            alertParamsUrl: '',
            selectedCheck: null,
            params: {}
        }, options);

        params = options.params;

        var nullCheckItem = $('#id_check_id option:first-child');
        nullCheckItem.attr('disabled', 'disabled');
        if (!options.selectedCheck) {
            $('#id_check_id').addClass('placeholder');
            nullCheckItem.attr('selected', 'selected');
        }

        $('#id_check_id').on('change', function() {
            var checkId = $('#id_check_id option:selected').val();

            $(this).removeClass('placeholder');

            var data = [
                {name: 'check_id', value: checkId}
            ];

            IvetlWeb.showLoading();
            $.get(options.alertParamsUrl, data)
                .done(function(html) {
                    $('.alert-params').html(html);
                })
                .always(function() {
                    IvetlWeb.hideLoading();
                });
        });

        $('#id_check_id, #id_publisher_id').on('change', function() {
            var selectedCheck = $('#id_check_id option:selected');
            var selectedPublisher = $('#id_publisher_id option:selected');
            $('#id_name').val(selectedCheck.text() + ' for ' + selectedPublisher.text());
            checkForm();
        });

        $('#id_name').on('keyup', function() {
            checkForm();
        });

        $('#id_enabled').on('change', function() {
            checkForm();
        });

        $.each(params, function(index, param) {
            $('#id_param_' + param.name).on('keyup', function() {
                checkForm();
            });
        });
    };

    return {
        init: init
    };

})();
