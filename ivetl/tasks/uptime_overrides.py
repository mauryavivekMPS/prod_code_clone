import json
from ivetl.models import UptimeOverride, UptimeCheckMetadata, UptimeCheckStat
from ivetl.celery import app
from ivetl import utils


def _get_matching_checks(override):
    match_expression = json.loads(override.match_expression_json)

    matching_checks = []
    for check_metadata in UptimeCheckMetadata.objects.all():

        add_check = True
        for attribute_name, values in match_expression.items():
            if values:
                value_for_this_check = str(getattr(check_metadata, attribute_name))
                if value_for_this_check not in values:
                    add_check = False

        if add_check:
            matching_checks.append((check_metadata.publisher_id, check_metadata.check_id))

    return matching_checks


@app.task
def apply_override(override_id):
    override = UptimeOverride.objects.get(override_id=override_id)
    matching_checks = _get_matching_checks(override)

    total_seconds = 60 * 60 * 24

    for publisher_id, check_id in matching_checks:
        for date in utils.day_range(override.start_date, override.end_date):

            try:
                stat = UptimeCheckStat.objects.get(
                    publisher_id=publisher_id,
                    check_id=check_id,
                    check_date=date,
                )

                # zero out down, and set anything less than up to unknown
                stat.total_down_sec = 0
                stat.total_unknown_sec = total_seconds - stat.original_total_up_sec
                stat.override = True
                stat.save()

            except UptimeCheckStat.DoesNotExist:
                pass


@app.task
def revert_and_delete_override(override_id):
    override = UptimeOverride.objects.get(override_id=override_id)
    matching_checks = _get_matching_checks(override)

    for publisher_id, check_id in matching_checks:
        for date in utils.day_range(override.start_date, override.end_date):
            try:
                stat = UptimeCheckStat.objects.get(
                    publisher_id=publisher_id,
                    check_id=check_id,
                    check_date=date,
                )

                # simply set back to original values
                stat.avg_response_ms = stat.original_avg_response_ms
                stat.total_up_sec = stat.original_total_up_sec
                stat.total_down_sec = stat.original_total_down_sec
                stat.total_unknown_sec = stat.original_total_unknown_sec
                stat.override = False
                stat.save()

            except UptimeCheckStat.DoesNotExist:
                pass

    override.delete()
