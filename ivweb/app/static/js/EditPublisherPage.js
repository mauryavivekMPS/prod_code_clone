var EditPublisherPage = (function() {
    var publisherId;
    var isNew;
    var validateCrossrefUrl;
    var validateIssnUrl;
    var addIssnValuesUrl;
    var buildingPollUrl;
    var buildingSuccessUrl;
    var buildingErrorUrl;

    var csrfToken;
    var isDemo;
    var convertFromDemo;
    var previousStatus;

    var publishedArticlesProduct = false;
    var articleCitationsProduct = false;
    var rejectedManuscriptsProduct = false;
    var cohortArticlesProduct = false;
    var cohortCitationsProduct = false;
    var institutionsProduct = false;
    var socialProduct = false;
    var metaProduct = false;

    var enableSubmit = function() {
        $('.submit-button.save-button').removeClass('disabled').prop('disabled', false);
    };

    var disableSubmit = function() {
        $('.submit-button.save-button').addClass('disabled').prop('disabled', true);
    };

    var enableSubmitForApproval = function() {
        $('.submit-button.submit-for-approval-button').removeClass('disabled').prop('disabled', false);
        $('.submit-button.convert-to-publisher-button').removeClass('disabled').prop('disabled', false);
    };

    var disableSubmitForApproval = function() {
        $('.submit-button.submit-for-approval-button').addClass('disabled').prop('disabled', true);
        $('.submit-button.convert-to-publisher-button').addClass('disabled').prop('disabled', true);
    };

    var checkForm = function() {

        var name = $("#id_name").val();
        var hasName = name !== '';

        var hasStartDate = false;
        if (isDemo) {
            var startDate = $("#id_start_date").val();
            hasStartDate = startDate !== '';
        }

        var publisherId = $("#id_publisher_id").val();
        var email = $("#id_email").val();
        var hasBasics = publisherId !== '' && name !== '' && email !== '';

        var hasValidScopusKeys = true;
        if (isNew && !isDemo) {
            var numScopusKeys = parseInt($('#id_num_scopus_keys').val());
            if (isNaN(numScopusKeys) || numScopusKeys < 0) {
                hasValidScopusKeys = false;
            }
        }

        var impactVizor = $('#id_impact_vizor_product_group').is(':checked');
        var usageVizor = $('#id_usage_vizor_product_group').is(':checked');
        var socialVizor = $('#id_social_vizor_product_group').is(':checked');
        var metaVizor = $('#id_meta_vizor_product_group').is(':checked');
        var atLeastOneProduct = impactVizor || usageVizor || socialVizor || metaVizor;

        var hasReportsDetails = true;
        if (isNew) {
            var reportsUsername = $('#id_reports_username').val();
            var reportsPassword = $('#id_reports_password').val();
            var reportsProject = $('#id_reports_project').val();

            if (publisherDemoMode()) {
                hasReportsDetails = reportsProject !== '';
            }
            else {
                hasReportsDetails = reportsUsername && reportsPassword && reportsProject;
            }
        }

        var crossref = true;
        var savableCrossref = true;
        if (useCrossref()) {
            var username = $('#id_crossref_username').val();
            var password = $('#id_crossref_password').val();
            var validated = $('.validate-crossref-checkmark').is(':visible');

            if (isDemo) {
                if (username || password) {
                    savableCrossref = username && password && validated;
                }
            }

            crossref = username && password && validated;
        }

        var validIssns = true;
        var savableIssns = true;
        var validMonthsFree = true;
        if (publishedArticlesProduct) {
            var gotOne = false;
            $('.issn-values-row').each(function () {
                var row = $(this);
                if (row.find('.validate-issn-checkmark').is(':visible')) {
                    gotOne = true;
                }
                else {
                    if (isDemo) {
                        if (!isIssnRowEmpty(row)) {
                            savableIssns = false;
                        }
                    }

                    if (gotOne && isIssnRowEmpty(row)) {
                        // let it slide
                    }
                    else {
                        validIssns = false;
                    }
                }

                var index = row.attr('index');
                if (useMonthsFree(index)) {
                    var months = parseInt($('.issn-values-months-row-' + index + ' .months-until-free').val());
                    if (isNaN(months) || months <= 0) {
                        validMonthsFree = false;
                    }
                }
            });
        }

        var validCohortIssns = true;
        var savableCohortIssns = true;
        var validMonthsFreeCohort = true;
        if (cohortArticlesProduct) {
            var gotOne = false;
            $('.issn-values-cohort-row').each(function () {
                var row = $(this);
                if (row.find('.validate-issn-checkmark').is(':visible')) {
                    gotOne = true;
                }
                else {
                    if (isDemo) {
                        if (!isIssnRowEmpty(row)) {
                            savableCohortIssns = false;
                        }
                    }

                    if (isIssnRowEmpty(row)) {
                        // let it slide, empty and zero rows is fine, the only thing that isn't is invalid data
                    }
                    else {
                        validCohortIssns = false;
                        return false;
                    }
                }

                var index = row.attr('index');
                if (useMonthsFree(index)) {
                    var months = parseInt($('.issn-values-months-cohort-row-' + index + ' .months-until-free').val());
                    if (isNaN(months) || months <= 0) {
                        validMonthsFreeCohort = false;
                    }
                }
            });
        }

        var validACDatabases = true;
        if (institutionsProduct && hasHighWire()) {
            if (!$('#id_ac_databases').val()) {
                validACDatabases = false;
            }
        }

        if (isDemo) {

            var atLeastOneRejectedArticlesUpload = true;
            if (rejectedManuscriptsProduct) {
                if ($('.rejected-manuscripts-controls table.all-files-table > tbody > tr.validated-file').length > 0) {
                    $('.rejected-articles-upload-requirement').addClass('satisfied');
                }
                else {
                    $('.rejected-articles-upload-requirement').removeClass('satisfied');
                    atLeastOneRejectedArticlesUpload = false;
                }
            }

            if (hasName) {
                $('.name-requirement').addClass('satisfied');
            }
            else {
                $('.name-requirement').removeClass('satisfied');
            }

            if (hasStartDate) {
                $('.date-requirement').addClass('satisfied');
            }
            else {
                $('.date-requirement').removeClass('satisfied');
            }

            if (atLeastOneProduct) {
                $('.product-requirement').addClass('satisfied');
            }
            else {
                $('.product-requirement').removeClass('satisfied');
            }

            if (crossref) {
                $('.crossref-requirement').addClass('satisfied');
            }
            else {
                $('.crossref-requirement').removeClass('satisfied');
            }

            if (validIssns) {
                $('.issns-requirement').addClass('satisfied');
            }
            else {
                $('.issns-requirement').removeClass('satisfied');
            }

            if (validCohortIssns) {
                $('.cohort-issns-requirement').addClass('satisfied');
            }
            else {
                $('.cohort-issns-requirement').removeClass('satisfied');
            }

            if (validMonthsFree) {
                $('.months-free-requirement').addClass('satisfied');
            }
            else {
                $('.months-free-requirement').removeClass('satisfied');
            }

            if (validMonthsFreeCohort) {
                $('.months-free-cohort-requirement').addClass('satisfied');
            }
            else {
                $('.months-free-cohort-requirement').removeClass('satisfied');
            }

            if (hasName && savableCrossref && savableIssns && savableCohortIssns) {
                enableSubmit();
            }
            else {
                disableSubmit();
            }

            if (hasBasics && hasStartDate && atLeastOneProduct && atLeastOneRejectedArticlesUpload && crossref && validIssns && validCohortIssns && validMonthsFree && validMonthsFreeCohort && validACDatabases) {
                enableSubmitForApproval();
            }
            else {
                disableSubmitForApproval();
            }
        }
        else {
            if (hasBasics && hasValidScopusKeys && atLeastOneProduct && hasReportsDetails && crossref && validIssns && validCohortIssns && validMonthsFree && validMonthsFreeCohort && validACDatabases) {
                enableSubmit();
            }
            else {
                disableSubmit();
            }
        }
    };

    var updateProductControls = function() {
        publishedArticlesProduct = false;
        articleCitationsProduct = false;
        rejectedManuscriptsProduct = false;
        cohortArticlesProduct = false;
        cohortCitationsProduct = false;
        institutionsProduct = false;
        socialProduct = false;
        metaProduct = false

        if ($('#id_impact_vizor_product_group').is(':checked')) {
            publishedArticlesProduct = true;
            articleCitationsProduct = true;
            rejectedManuscriptsProduct = true;
            cohortArticlesProduct = true;
            cohortCitationsProduct = true;
        }

        if ($('#id_usage_vizor_product_group').is(':checked')) {
            publishedArticlesProduct = true;
            institutionsProduct = true;
        }

        if ($('#id_social_vizor_product_group').is(':checked')) {
            publishedArticlesProduct = true;
            socialProduct = true;
        }

        if (publishedArticlesProduct) {
            $('.published-articles-controls').fadeIn(200);
        }
        else {
            $('.published-articles-controls').fadeOut(100);
        }

        if (rejectedManuscriptsProduct) {
            $('.rejected-manuscripts-controls').fadeIn(200);
        }
        else {
            $('.rejected-manuscripts-controls').fadeOut(100);
        }

        if (cohortArticlesProduct) {
            $('.cohort-articles-controls').fadeIn(200);
        }
        else {
            $('.cohort-articles-controls').fadeOut(100);
        }

        if (institutionsProduct) {
            $('.institutions-controls').fadeIn(200);
        }
        else {
            $('.institutions-controls').fadeOut(100);
        }
        updateACDatabasesControls();
    };

    var hasHighWire = function() {
        return $('#id_hw_addl_metadata_available').is(':checked');
    };

    var updateHighWireControls = function() {
        if (hasHighWire()) {
            $('.highwire-controls').fadeIn(200);
        }
        else {
            $('.highwire-controls').fadeOut(100);
        }
        updateACDatabasesControls();
    };

    var updateACDatabasesControls = function() {
        if (!(institutionsProduct && hasHighWire())) {
            $('#id_ac_databases').val('');
        }
    };

    var updateStatusControls = function() {
        if ($('#id_status').val() != previousStatus) {
            $('.status-controls').fadeIn(200);
        }
        else {
            $('.status-controls').fadeOut(100);
        }
    };

    var useCrossref = function() {
        return $('#id_use_crossref').is(':checked');
    };

    var updateCrossrefControls = function() {
        if (useCrossref()) {
            $('.crossref-controls').fadeIn(200);
        }
        else {
            $('.crossref-controls').fadeOut(100);
            $('#id_crossref_username').val('');
            $('#id_crossref_password').val('');
        }
    };

    var publisherDemoMode = function() {
        return $('#id_demo').is(':checked');
    };

    var updateReportsLoginControls = function() {
        if (publisherDemoMode()) {
            $('.reports-login-controls').fadeOut(200);
        }
        else {
            $('.reports-login-controls').fadeIn(100);
        }
    };

    var updateValidateCrossrefButton = function() {
        var username = $('#id_crossref_username').val();
        var password = $('#id_crossref_password').val();
        var button = $('.validate-crossref-button');
        var message = $('.crossref-error-message');
        var checkmark = $('.validate-crossref-checkmark');
        var row = $('.crossref-form-row');

        message.hide();
        checkmark.hide();
        row.removeClass('error');

        if (username || password) {
            button.show();
        }
        else {
            button.hide();
        }
    };

    var checkCrossref = function() {
        var button = $('.validate-crossref-button');
        var loading = $('.validate-crossref-loading');

        button.hide();
        loading.show();

        var username = $('#id_crossref_username');
        var password = $('#id_crossref_password');
        var row = $('.crossref-form-row');
        var message = $('.crossref-error-message');
        var checkmark = $('.validate-crossref-checkmark');

        var data = [
            {name: 'username', value: username.val()},
            {name: 'password', value: password.val()}
        ];

        $.get(validateCrossrefUrl, data)
            .done(function(html) {
                loading.hide();
                if (html == 'ok') {
                    row.removeClass('error');
                    button.hide();
                    message.hide();
                    button.hide();
                    checkmark.show();
                }
                else {
                    row.addClass('error');
                    message.show();
                    button.show();
                    checkmark.hide();
                    button.addClass('disabled').show();
                }
                checkForm();
            });

        return false;
    };

    var useMonthsFree = function(index) {
        return $('.issn-values-months-row-' + index + ' .use-months-until-free').is(':checked');
    };

    var updateMonthsFreeControls = function(index) {
        var row = $('.issn-values-months-row-' + index);
        if (useMonthsFree(index)) {
            row.find('.months-until-free').removeClass('disabled').prop('disabled', false).attr('placeholder', '0');
            row.find('.months-free-text').removeClass('disabled');
            $('.months-free-controls').fadeIn(200);
        }
        else {
            row.find('.months-until-free').addClass('disabled').prop('disabled', true).val('').attr('placeholder', '');
            row.find('.months-free-text').addClass('disabled');

            var atLeastOneMonthsFree = false;
            $('.issn-values-months-row .use-months-until-free').each(function () {
                if ($(this).is(':checked')) {
                    atLeastOneMonthsFree = true;
                    return false;
                }
            });
            if (atLeastOneMonthsFree) {
                $('.months-free-controls').fadeIn(200);
            }
            else {
                $('.months-free-controls').fadeOut(100);
            }
        }
    };

    var useMonthsFreeCohort = function(index) {
        return $('.issn-values-months-cohort-row-' + index + ' .use-months-until-free').is(':checked');
    };

    var updateMonthsFreeCohortControls = function(index) {
        var row = $('.issn-values-months-cohort-row-' + index);
        if (useMonthsFreeCohort(index)) {
            row.find('.months-until-free').removeClass('disabled').prop('disabled', false);
            row.find('.months-free-text').removeClass('disabled');
            $('.months-free-cohort-controls').fadeIn(200);
        }
        else {
            row.find('.months-until-free').addClass('disabled').prop('disabled', true).val('');
            row.find('.months-free-text').addClass('disabled');

            var atLeastOneMonthsFree = false;
            $('.issn-values-months-cohort-row .use-months-until-free').each(function () {
                if ($(this).is(':checked')) {
                    atLeastOneMonthsFree = true;
                    return false;
                }
            });
            if (atLeastOneMonthsFree) {
                $('.months-free-cohort-controls').fadeIn(200);
            }
            else {
                $('.months-free-cohort-controls').fadeOut(100);
            }
        }
    };

    var isIssnRowEmpty = function(row) {
        var index = row.attr('index');
        var electronicIssn = row.find('#id_electronic_issn_' + index).val();
        var printIssn = row.find('#id_print_issn_' + index).val();
        var journalCode = row.find('#id_journal_code_' + index).val();
        return !electronicIssn && !printIssn && !journalCode;
    };

    var wireUpValidateIssnButton = function(mainRowSelector, monthsRowSelector, benchpressRowSelector, index, cohort) {
        var mainRow = $(mainRowSelector);
        var monthsRow = $(monthsRowSelector);
        var benchpressRow = $(benchpressRowSelector);
        var button = mainRow.find('.validate-issn-button');

        button.on('click', function() {
            var usingJournal = hasHighWire() && !cohort;
            var loading = mainRow.find('.validate-issn-loading');
            var checkmark = mainRow.find('.validate-issn-checkmark');
            var message = mainRow.find('.issn-error-message');

            button.hide();
            loading.show();

            var electronicIssn = mainRow.find('#id_electronic_issn_' + index).val();
            var printIssn = mainRow.find('#id_print_issn_' + index).val();

            if (usingJournal) {
                var journalCode = mainRow.find('#id_journal_code_' + index).val();
            }

            var useMonthsUntilFree = monthsRow.find('#id_use_months_until_free_' + index).is(':checked') ? 'on' : '';
            var monthsUntilFree = monthsRow.find('#id_months_until_free_' + index).val();
            var useBenchpress = benchpressRow.find('#id_use_benchpress_' + index).is(':checked') ? 'on' : '';

            var setIssnError = function(error) {
                mainRow.addClass('error');
                message.html('<li>' + error + '</li>').show();
                button.show();
                checkmark.hide();
                button.addClass('disabled').show();
            };

            var setIssnWarning = function(warning) {
                message.html('<li>' + warning + '</li>').show();
                checkmark.show();
            };

            // quick local checks for blank entries
            if (electronicIssn === '' || printIssn === '' || (usingJournal && journalCode === '')) {
                loading.hide();
                setIssnError('All ISSN fields need a value.');
                return false;
            }

            var data = [
                {name: 'electronic_issn', value: electronicIssn},
                {name: 'print_issn', value: printIssn},
                {name: 'print_issn', value: printIssn},
                {name: 'use_months_until_free', value: useMonthsUntilFree},
                {name: 'months_until_free', value: monthsUntilFree},
                {name: 'use_benchpress', value: useBenchpress},
                {name: 'csrfmiddlewaretoken', value: csrfToken}
            ];

            if (usingJournal) {
                data.push(
                    {name: 'journal_code', value: journalCode}
                );
            }

            $.getJSON(validateIssnUrl, data)
                .done(function(json) {
                    loading.hide();
                    if (json.status === 'ok') {
                        mainRow.removeClass('error');
                        button.hide();
                        message.hide();
                        button.hide();
                        checkmark.show();
                    }
                    else if (json.status === 'error') {
                        setIssnError(json.error_message);
                    }
                    else if (json.status === 'warning') {
                        mainRow.removeClass('error');
                        setIssnWarning(json.warning_message);
                    }
                    checkForm();
                });

            return false;
        });
    };

    var wireUpIssnControls = function(mainRowSelector, monthsRowSelector, benchpressRowSelector, index, cohort) {
        var mainRow = $(mainRowSelector);
        mainRow.find('input').on('keyup', function() {
            mainRow.find('.validate-issn-checkmark').hide();
            mainRow.find('.validate-issn-button').show();
            checkForm();
        });

        $(monthsRowSelector).find('input').on('keyup', checkForm);

        if (!cohort) {
            $('#id_hw_addl_metadata_available').on('change', function () {
                if (hasHighWire()) {
                    mainRow.find('.validate-issn-checkmark').hide();
                    mainRow.find('.validate-issn-button').show();
                }
                checkForm();
            });
        }
    };

    var wireUpDeleteIssnButton = function(mainRowSelector, monthsRowSelector, benchpressRowSelector, index, cohort) {
        var mainRow = $(mainRowSelector);
        mainRow.find('.delete-issn-button').on('click', function() {
            mainRow.remove();
            $(monthsRowSelector).remove();
            checkForm();
            return false;
        });
    };

    var showSetupStatusModal = function(isNew) {
        $('#creating-publisher-modal').modal({
            backdrop: 'static',
            keyboard: false
        });

        setInterval(function() {
            $.getJSON(buildingPollUrl)
                .done(function(json) {
                    if (isNew) {
                        if (json.reports_setup_status === 'completed') {
                            window.location = buildingSuccessUrl;
                        }
                        else if (json.reports_setup_status === 'error') {
                            window.location = buildingErrorUrl + '?from=reports-setup-error';
                        }
                    }
                    else {
                        if (json.reports_setup_status === 'completed') {
                            window.location = buildingSuccessUrl;
                        }
                        else if (json.reports_setup_status === 'error') {
                            window.location = buildingErrorUrl + '?from=reports-update-error';
                        }
                    }
                });
        }, 1000);
    };

    var submit = function(options) {
        options = $.extend({
            submitForApproval: false,
            convertToPublisher: false
        }, options);

        var issnValues = [];
        $('.issn-values-row').each(function() {
            var row = $(this);
            if (!isIssnRowEmpty(row)) {
                var index = row.attr('index');
                issnValues.push({
                    electronic_issn: row.find('#id_electronic_issn_' + index).val(),
                    print_issn: row.find('#id_print_issn_' + index).val(),
                    journal_code: row.find('#id_journal_code_' + index).val(),
                    use_months_until_free: $('.issn-values-months-row #id_use_months_until_free_' + index).is(':checked') ? 'on' : '',
                    months_until_free: $('.issn-values-months-row #id_months_until_free_' + index).val(),
                    use_benchpress: $('.issn-values-benchpress-row #id_use_benchpress_' + index).is(':checked') ? 'on' : '',
                    use_pubmed_override: $('.issn-values-pubmed-row #id_use_pubmed_override_' + index).is(':checked') ? 'on' : '',
                    skip_rule: $('.issn-values-skip-rule-row #id_skip_rule_' + index).val(),
                    index: index
                });
            }
        });
        $('#id_issn_values').val(JSON.stringify(issnValues));

        var issnCohortValues = [];
        $('.issn-values-cohort-row').each(function() {
            var row = $(this);
            if (!isIssnRowEmpty(row)) {
                var index = row.attr('index');
                issnCohortValues.push({
                    electronic_issn: row.find('#id_electronic_issn_' + index).val(),
                    print_issn: row.find('#id_print_issn_' + index).val(),
                    use_months_until_free: $('.issn-values-months-cohort-row #id_use_months_until_free_' + index).is(':checked') ? 'on' : '',
                    months_until_free: $('.issn-values-months-cohort-row #id_months_until_free_' + index).val(),
                    skip_rule: $('.issn-values-skip-rule-cohort-row #id_skip_rule_cohort_' + index).val(),
                    index: index
                });
            }
        });
        $('#id_issn_values_cohort').val(JSON.stringify(issnCohortValues));

        var f = $('#hidden-publisher-form');
        f.find('input[name="publisher_id"]').val($('#id_publisher_id').val());
        f.find('input[name="name"]').val($('#id_name').val());
        f.find('input[name="issn_values"]').val($('#id_issn_values').val());
        f.find('input[name="email"]').val($('#id_email').val());
        f.find('input[name="note"]').val($('#id_note').val());
        f.find('input[name="use_crossref"]').val($('#id_use_crossref').is(':checked') ? 'on' : '');
        f.find('input[name="crossref_username"]').val($('#id_crossref_username').val());
        f.find('input[name="crossref_password"]').val($('#id_crossref_password').val());
        f.find('input[name="hw_addl_metadata_available"]').val($('#id_hw_addl_metadata_available').is(':checked') ? 'on' : '');
        f.find('input[name="scopus_api_keys"]').val($('#id_scopus_api_keys').val());
        f.find('input[name="demo"]').val($('#id_demo').is(':checked') ? 'on' : '');
        f.find('input[name="pilot"]').val($('#id_pilot').is(':checked') ? 'on' : '');
        f.find('input[name="ac_databases"]').val($('#id_ac_databases').val());
        f.find('input[name="issn_values_cohort"]').val($('#id_issn_values_cohort').val());
        f.find('input[name="reports_username"]').val($('#id_reports_username').val());
        f.find('input[name="reports_password"]').val($('#id_reports_password').val());
        f.find('input[name="reports_project"]').val($('#id_reports_project').val());
        f.find('input[name="demo_id"]').val($('#id_demo_id').val());
        f.find('input[name="start_date"]').val($('#id_start_date').val());
        f.find('input[name="demo_notes"]').val($('#id_demo_notes').val());
        f.find('input[name="message"]').val($('#id_message').val());
        f.find('input[name="impact_vizor_product_group"]').val($('#id_impact_vizor_product_group').is(':checked') ? 'on' : '');
        f.find('input[name="usage_vizor_product_group"]').val($('#id_usage_vizor_product_group').is(':checked') ? 'on' : '');
        f.find('input[name="social_vizor_product_group"]').val($('#id_social_vizor_product_group').is(':checked') ? 'on' : '');
        f.find('input[name="meta_vizor_product_group"]').val($('#id_meta_vizor_product_group').is(':checked') ? 'on' : '');
        f.find('input[name="num_scopus_keys"]').val($('#id_num_scopus_keys').val());
        f.find('input[name="modify_tableau"]').val($('#id_modify_tableau').is(':checked') ? 'on' : '');
        f.find('input[name="modify_tableau_new"]').val($('#id_modify_tableau_new').is(':checked') ? 'on' : '');

        if (options.submitForApproval) {
            f.find('input[name="status"]').val('submitted-for-review');
        }
        else {
            f.find('input[name="status"]').val($('#id_status option:selected').val());
        }

        if (options.convertToPublisher) {
            f.find('input[name="convert_to_publisher"]').val('on');
        }
        else {
            f.find('input[name="convert_to_publisher"]').val('');
        }

        f.submit();
    };

    var init = function(options) {
        options = $.extend({
            publisherId: '',
            validateCrossrefUrl: '',
            validateIssnUrl: '',
            addIssnValuesUrl: '',
            buildingPollUrl: '',
            buildingSuccessUrl: '',
            buildingErrorUrl: '',
            csrfToken: '',
            isDemo: false,
            convertFromDemo: false,
            previousStatus: ''
        }, options);

        publisherId = options.publisherId;
        validateCrossrefUrl = options.validateCrossrefUrl;
        validateIssnUrl = options.validateIssnUrl;
        addIssnValuesUrl = options.addIssnValuesUrl;
        buildingPollUrl = options.buildingPollUrl;
        buildingSuccessUrl = options.buildingSuccessUrl;
        buildingErrorUrl = options.buildingErrorUrl;
        csrfToken = options.csrfToken;
        isDemo = options.isDemo;
        convertFromDemo = options.convertFromDemo;
        previousStatus = options.previousStatus;

        isNew = publisherId === '';

        $('#id_publisher_id, #id_name, #id_email').on('keyup', checkForm);
        $('#id_reports_username, #id_reports_password, #id_reports_project').on('keyup', checkForm);
        $('#id_pilot').on('change', checkForm);

        $('#id_start_date').datepicker({
            autoclose: true
        });

        $('#id_start_date').on('change', checkForm);

        if (isNew) {
            $('#id_reports_password').show();
        }
        $('.set-reports-password-link a').click(function() {
            $('.set-reports-password-link').hide();
            $('#id_reports_password').show().focus();
            return false;
        });

        $('#id_impact_vizor_product_group, #id_usage_vizor_product_group, #id_social_vizor_product_group, #id_meta_vizor_product_group').on('change', function() {
            updateProductControls();
            checkForm();
        });
        updateProductControls();

        $('#id_ac_databases').on('keyup', checkForm);

        $('#id_hw_addl_metadata_available').on('change', function() {
            updateHighWireControls();
            checkForm();
        });
        updateHighWireControls();

        $('#id_use_crossref').on('change', function() {
            updateCrossrefControls();
            checkForm();
        });
        updateCrossrefControls();

        $('#id_demo').on('change', function() {
            updateReportsLoginControls();
            checkForm();
        });
        updateReportsLoginControls();

        $('#id_status').on('change', function() {
            updateStatusControls();
            checkForm();
        });
        updateStatusControls();

        $('#id_crossref_username, #id_crossref_password').on('keyup', function() {
            updateValidateCrossrefButton();
            checkForm();
        });
        $('.validate-crossref-button').on('click', checkCrossref);

        $('.add-issn-button').on('click', function() {
            $.get(addIssnValuesUrl)
                .done(function(html) {
                    $('#issn-values-container').append(html);
                    updateHighWireControls();
                    updateProductControls();
                    checkForm();
                });
            return false;
        });

        $('.add-issn-cohort-button').on('click', function() {
            $.get(addIssnValuesUrl, [{name: 'cohort', value: 1}])
                .done(function(html) {
                    $('#issn-values-cohort-container').append(html);
                    checkForm();
                });
            return false;
        });

        $('.issn-values-months-row .use-months-until-free').on('change', function() {
            var index = $(this).attr('index');
            updateMonthsFreeControls(index);
            checkForm();
        });

        $('.issn-values-row').each(function() {
            var index = $(this).attr('index');
            updateMonthsFreeControls(index);
        });

        $('.issn-values-months-row .use-benchpress').on('change', function() {
            checkForm();
        });

        $('.issn-values-months-cohort-row .use-months-until-free').on('change', function() {
            var index = $(this).attr('index');
            updateMonthsFreeCohortControls(index);
            checkForm();
        });

        $('.issn-values-cohort-row').each(function() {
            var index = $(this).attr('index');
            updateMonthsFreeCohortControls(index);
        });

        $('.submit-button.save-button').on('click', function(event) {
            submit();
            event.preventDefault();
            return false;
        });

        $('.submit-button.submit-for-approval-button').on('click', function(event) {
            submit({submitForApproval: true});
            event.preventDefault();
            return false;
        });

        $('.submit-button.convert-to-publisher-button').on('click', function(event) {
            submit({convertToPublisher: true});
            event.preventDefault();
            return false;
        });

        if (isDemo) {
            var m = $('#confirm-archive-demo-modal');

            m.find('.confirm-archive-demo-button').on('click', function() {
                IvetlWeb.showLoading();
                m.modal('hide');
                $('#archive-demo-form').submit();
            });

            $('.archive-demo').on('click', function() {
                m.modal();
            });
        }

        checkForm();
    };

    return {
        wireUpValidateIssnButton: wireUpValidateIssnButton,
        wireUpDeleteIssnButton: wireUpDeleteIssnButton,
        wireUpIssnControls: wireUpIssnControls,
        showBuildingReportsModal: showSetupStatusModal,
        checkForm: checkForm,
        init: init
    };

})();
