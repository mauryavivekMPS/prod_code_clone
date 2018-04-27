import os
import csv
from decimal import Decimal, InvalidOperation
from dateutil.parser import parse
from ivetl.validators.base import BaseValidator
from ivetl.models import ProductBundle
from ivetl import utils


class SubscriptionPricingValidator(BaseValidator):

    def validate_files(self, files, issns=[], publisher_id=None, crossref_username=None, crossref_password=None, increment_count_func=None, second_level_validation=False):
        errors = []
        total_count = 0
        for f in files:
            file_name = os.path.basename(f)
            try:
                encoding = utils.guess_encoding(f)
                with open(f, encoding=encoding) as tsv:
                    count = 0
                    for line in csv.reader(tsv, delimiter='\t'):
                        if line:
                            if increment_count_func:
                                count = increment_count_func(count)
                            else:
                                count += 1

                            # skip header row
                            if count == 1:
                                continue

                            # check for number of fields
                            if len(line) != 6:
                                errors.append(self.format_error(file_name, count - 1, "Incorrect number of fields, skipping other validation"))
                                continue

                            if not line[0]:
                                errors.append(self.format_error(file_name, count - 1, "Membership number is missing"))

                            if not line[1]:
                                errors.append(self.format_error(file_name, count - 1, "Year is a required field"))

                            try:
                                year = int(line[1])
                                if year < 2000:
                                    raise ValueError
                            except ValueError:
                                errors.append(self.format_error(file_name, count - 1, "Year must be a four digit integer"))

                            if not line[2]:
                                errors.append(self.format_error(file_name, count - 1, "Bundle name is missing"))

                            try:
                                ProductBundle.objects.get(publisher_id=publisher_id, bundle_name=line[2])
                            except ProductBundle.DoesNotExist:
                                errors.append(self.format_error(file_name, count - 1, "Bundle name not found in database"))

                            if line[3] and line[3] not in ('y', 'n', 'Y', 'N'):
                                errors.append(self.format_error(file_name, count - 1, "Trial field must be Y or N"))

                            if line[4]:
                                try:
                                    parse(line[4])
                                except ValueError:
                                    errors.append(self.format_error(file_name, count - 1, "Trial expiration date must be MM/DD/YY"))

                            if not line[5]:
                                errors.append(self.format_error(file_name, count - 1, "Amount field is required"))
                            else:
                                try:
                                    Decimal(line[5])
                                except (ValueError, InvalidOperation):
                                    errors.append(self.format_error(file_name, count - 1, "Amount must be a valid decimal"))

                        if len(errors) > self.MAX_ERRORS:
                            break

                    total_count += count

            except UnicodeDecodeError:
                errors.append(self.format_error(file_name, 0, "This file is not a recognized encoding, skipping further validation"))

        return total_count, errors
