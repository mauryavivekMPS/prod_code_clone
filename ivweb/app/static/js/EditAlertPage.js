var EditAlertPage = (function() {
    var alertParamsUrl;
    var alertFiltesUrl;
    var checkChoicesUrl;
    var params = [];
    var filters = [];

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

    var setParams = function(newParams) {
        params = newParams;
        $.each(params, function(index, param) {
            $('#id_param_' + param.name).on('keyup', function() {
                checkForm();
            });
        });
    };

    var setFilters = function(newFilters) {
        filters = newFilters;
        $.each(filters, function(index, filter) {
            var filterElement = $('#id_filter_' + filter.name);

            filterElement.typeahead({
                source: filter.filter_values,
                showHintOnFocus: true,
                autoSelect: true
            });

            filterElement.on('keyup', function() {
                checkForm();
            });
        });
    };

    var updateFilters = function() {
        var checkId = $('#id_check_id option:selected').val();
        var publisherId = $("#id_publisher_id option:selected").val();

        var data = [
            {name: 'check_id', value: checkId},
            {name: 'publisher_id', value: publisherId}
        ];

        IvetlWeb.showLoading();

        $.get(alertFiltersUrl, data)
            .done(function(html) {
                $('.alert-filters').html(html);
            })
            .always(function() {
                IvetlWeb.hideLoading();
            });
    };

    var onPublisherOrCheckChange = function() {
        if ($('#id_check_id option').length > 0) {
            updateAlertName();
            updateParams();
            updateFilters();
        }
        else {
            $('#id_name').val('');
        }
        checkForm();
    };

    var updateCheckChoices = function() {
        var data = [
            {name: 'publisher_id', value: $('#id_publisher_id option:selected').val()}
        ];

        $.get(checkChoicesUrl, data)
            .done(function(html) {
                $('.check-control-container').html(html);
                $('#id_check_id').on('change', function() {
                    onPublisherOrCheckChange();
                });
                onPublisherOrCheckChange();
            });
    };

    var updateParams = function() {
        var checkId = $('#id_check_id option:selected').val();

        $(this).removeClass('placeholder');

        var data = [
            {name: 'check_id', value: checkId}
        ];

        IvetlWeb.showLoading();
        $.get(alertParamsUrl, data)
            .done(function(html) {
                $('.alert-params').html(html);
            })
            .always(function() {
                IvetlWeb.hideLoading();
            });
    };

    var updateAlertName = function() {
        var selectedCheck = $('#id_check_id option:selected');
        var selectedPublisher = $('#id_publisher_id option:selected');
        $('#id_name').val(selectedCheck.text() + ' for ' + selectedPublisher.text());
    };

    var init = function(options) {
        options = $.extend({
            alertParamsUrl: '',
            alertFiltersUrl: '',
            checkChoicesUrl: '',
            selectedCheck: null
        }, options);

        alertParamsUrl = options.alertParamsUrl;
        alertFiltersUrl = options.alertFiltersUrl;
        checkChoicesUrl = options.checkChoicesUrl;

        $('#id_publisher_id').on('change', function() {
            updateCheckChoices();
        });
        updateCheckChoices();

        $('#id_name').on('keyup', function() {
            checkForm();
        });

        $('#id_enabled').on('change', function() {
            checkForm();
        });
    };

    return {
        setParams: setParams,
        setFilters: setFilters,
        checkForm: checkForm,
        init: init
    };

})();
