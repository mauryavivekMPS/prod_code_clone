var EditAlertPage = (function() {
    var alertParamsUrl;
    var alertFiltersUrl;
    var checkChoicesUrl;
    var params = [];
    var filters = [];

    var isIntegerValue = function(value) {
        return !isNaN(value) && parseInt(Number(value)) == value && !isNaN(parseInt(value, 10)) && parseInt(value) > 0;
    };

    var isPercentageValue = function(value) {
        return isIntegerValue(value) && parseInt(value) > 0;
    };

    var checkForm = function() {
        var checkId = $("#id_check_id option:selected").val();
        var publisherId = $("#id_publisher_id option:selected").val();
        var name = $('#id_name').val();
        var emails = $('#id_comma_separated_emails').val();

        if (name) {
            $('.name-requirement').addClass('satisfied');
        }
        else {
            $('.name-requirement').removeClass('satisfied');
        }

        if (emails) {
            $('.email-requirement').addClass('satisfied');
        }
        else {
            $('.email-requirement').removeClass('satisfied');
        }

        var gotParamValues = true;
        $.each(params, function(index, param) {
            var requirement = $('.' + param.name + '-requirement');
            var value = $('#id_param_' + param.name).val();

            var isValid = false;
            if (value) {
                if (param.type == 'integer') {
                    isValid = isIntegerValue(value);
                }
                else if (param.type == 'percentage') {
                    isValid = isPercentageValue(value);
                }
            }

            if (value && isValid) {
                requirement.addClass('satisfied');
            }
            else {
                requirement.removeClass('satisfied');
                gotParamValues = false;
            }
        });

        if (publisherId && checkId && name && emails && gotParamValues) {
            $('.submit-button').removeClass('disabled').prop('disabled', false);
        }
        else {
            $('.submit-button').addClass('disabled').prop('disabled', false);
        }
    };

    var setParams = function(newParams) {
        params = newParams;
        $.each(params, function(index, param) {
            $('.requirements-items .param-requirement').remove();
            $('.requirements-items').append('<li class="' + param.name + '-requirement param-requirement">' + param.requirement_text + '<span class="lnr lnr-check checkmark"></span></li>');
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
            updateParams();
            updateFilters();
        }
        else {
            $('#id_name').val('');
        }
        checkForm();
    };

    var wireUpCheckChoices = function() {
        $('#id_check_id').on('change', function() {
            onPublisherOrCheckChange();
        });
    };

    var updateCheckChoices = function() {
        var data = [
            {name: 'publisher_id', value: $('#id_publisher_id option:selected').val()}
        ];

        $.get(checkChoicesUrl, data)
            .done(function(html) {
                $('.check-control-container').html(html);
                wireUpCheckChoices();
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
        if (!options.selectedCheck) {
            updateCheckChoices();
        }
        wireUpCheckChoices();

        $('#id_name, #id_comma_separated_emails').on('keyup', function() {
            checkForm();
        });

        $('#id_enabled').on('change', function() {
            checkForm();
        });

        var m = $('#confirm-archive-alert-modal');

        m.find('.confirm-archive-alert-button').on('click', function() {
            IvetlWeb.showLoading();
            m.modal('hide');
            $('#archive-alert-form').submit();
        });

        $('.archive-alert').on('click', function() {
            m.modal();
        });
    };

    return {
        setParams: setParams,
        setFilters: setFilters,
        checkForm: checkForm,
        init: init
    };

})();
