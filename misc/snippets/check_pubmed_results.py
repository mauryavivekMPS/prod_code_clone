#!/usr/bin/env python
import csv
import json
import os
os.sys.path.append(os.environ['IVETL_ROOT'])

from ivetl.connectors import CrossrefConnector
from ivetl.connectors import PubMedConnector

# utility script for generating PubMed / CrossRef API results
# for Rejected Article Algorithm analsyis
# VIZOR-224

crossref_base = 'https://api.crossref.org'
mailto = '?mailto=mgraham@highwirepress.com'
doi_lookup_only = False

inputfile_path = ('/iv/working/misc/'
    'RAT_Article_Data_Appeals_Removed_042019_MAjournals_edit_add_pubmed_results'
    '.tsv')

outputfile_path = ('/iv/working/misc/'
    'RAT_Article_Data_Appeals_Removed_042019_MAjournals_crosscheck_pubmed_api'
    '.tsv')

errorfile_path = ('/iv/working/misc/'
    'RAT_Article_Data_Appeals_Removed_042019_MAjournals_crosscheck_pubmed_api'
    '_errors.tsv')


crossref = CrossrefConnector()
pubmed = PubMedConnector()

article_expected = 0
meeting_abstract_expected = 0
article_not_in_pubmed = 0
meeting_abstract_in_pubmed = 0
rows_processed = 0
errors = 0
outrows = []
with open(inputfile_path,
        encoding='utf-8') as infile, open(outputfile_path, 'w',
        encoding='utf-8') as outfile, open(errorfile_path, 'w',
        encoding='utf-8') as errfile:

    inputreader = csv.reader(infile, delimiter='\t')
    outputwriter = csv.writer(outfile, delimiter='\t')
    errorwriter = csv.writer(errfile, delimiter='\t')

    header = None
    outheader = ['Outcome', 'In PubMed', '#PubMed Results']
    errheader = ['Error']

    for row in inputreader:
        if not header:
            header = row
            outheader.extend(header)
            outheader.append('CrossRef API URL')
            outheader.append('PubMed API URL')
            outputwriter.writerow(outheader)
            errheader.extend(header)
            errheader.append('CrossRef API URL')
            errheader.append('PubMed API URL')
            errheader.append('Missing CrossRef Metadata')
            errorwriter.writerow(errheader)
            continue

        doi = row[0]
        highlighted = row[2]
        rows_processed += 1

        if highlighted != 'Yes' and highlighted != 'No':
            print('Row missing highlight variable: {0}'.format(doi))
            continue

        url = crossref_base + '/works/' + doi + mailto

        article_response_text = crossref.get_with_retry(url)

        try:
            article_json = json.loads(article_response_text)
            article_json = article_json['message']
        except (ValueError, TypeError):
            print('failed to parse json for url: {0}'.format(url))
            outrow = ['JSON Parse Failure']
            outrow.extend(row)
            outrow.append(url)
            errors += 1
            errorwriter.writerow(outrow)
            continue

        pubmed_url = pubmed.citation_lookup_url(article_json)
        result = None
        if pubmed_url and not doi_lookup_only:
            pubmed_url_type = 'citation'
            print(pubmed_url)
            try:
                result = pubmed.search_single_citation(pubmed_url)
            except Exception as inst:
                print('Exception: {0}'.format(inst))
                errors += 1
                outrow = ['Exception: {0}'.format(inst)]
                outrow.extend(row)
                outrow.append(url)
                errorwriter.writerow(outrow)
                continue
            if (result and 'esearchresult' in result and
                'count' in result['esearchresult']):

                count = result['esearchresult']['count']
            try:
                count = int(count)
            except ValueError:
                print(('Non-Integer count value received from PubMed lookup: '
                    '{0}').format(count))
                outrow = ['PubMed Error - Count']
                outrow.extend(row)
                outrow.append(url)
                outrow.append(pubmed_url)
                errors += 1
                errorwriter.writerow(outrow)
                continue
            if count > 0:
                in_pubmed = 'True'
            else:
                in_pubmed = 'False'
        elif 'DOI' in article_json:
            pubmed_url = pubmed.doi_lookup_url(doi)
            pubmed_url_type = 'doi'
            print(pubmed_url)
            try:
                result = pubmed.search_single_citation(pubmed_url)
            except Exception as inst:
                print('Exception: {0}'.format(inst))
                errors += 1
                outrow = ['Exception: {0}'.format(inst)]
                outrow.extend(row)
                outrow.append(url)
                errorwriter.writerow(outrow)
                continue
            querytranslation = '{0}[All Fields]'.format(doi)
            count = 0
            if ('esearchresult' in result and
                'querytranslation' in result['esearchresult'] and
                result['esearchresult']['querytranslation'] == querytranslation and
                'count' in result['esearchresult']):
                count = result['esearchresult']['count']
                try:
                    count = int(count)
                except ValueError:
                    self.log(('Non-Integer count value received from PubMed lookup: '
                        '{0}, {1}').format(count, url))
            if count > 0:
                in_pubmed = 'True'
            else:
                in_pubmed = 'False'

        if highlighted == 'No' and in_pubmed == 'True':
            outcome = 'Correct - Article; in PubMed'
            article_expected += 1
        elif highlighted == 'Yes' and in_pubmed == 'False':
            outcome = 'Correct - Meeting Abstract; not in PubMed'
            meeting_abstract_expected += 1
        elif highlighted == 'No' and in_pubmed == 'False':
            outcome = 'Failure - Article; not in PubMed'
            article_not_in_pubmed += 1
        elif highlighted == 'Yes' and in_pubmed == 'True':
            outcome = 'Failure - Meeting Abstract; not in PubMed'
            meeting_abstract_in_pubmed += 1

        outrow = [outcome, in_pubmed, count]
        outrow.extend(row)
        outrow.append(url)
        outrow.append(pubmed_url)
        outputwriter.writerow(outrow)

        if not result:
            in_pubmed = 'Lookup Error'
            outrow = ['PubMed Error']
            outrow.extend(row)
            outrow.append(url)
            outrow.append(pubmed_url)
            if not pubmed_url:
                missing_metadata = []
                if not 'container-title' in article_json and not 'ISSN' in article_json:
                    missing_metadata.append('journal')
                if not 'volume' in article_json:
                    missing_metadata.append('volume')
                if not ('issue' in article_json or
                    ('journal-issue' in article_json and
                    'issue' in article_json['journal-issue'])):
                    missing_metadata.append('issue')
                if not 'page' in article_json:
                    missing_metadata.append('page')
                metadata = ', '.join(missing_metadata)
                outrow.append(missing_metadata)
            errors += 1
            errorwriter.writerow(outrow)
            continue

infile.close()
outfile.close()

print('Run complete')
print('counts:')
print('Rows processed: {0})'.format(rows_processed))
print('Errors rows: {0} ({1}))'.format(errors, errors / rows_processed))
print('Articles expected: {0} ({1}))'.format(article_expected,
    article_expected / rows_processed))
print('Meeting Abstracts expected: {0} ({1}))'.format(
    meeting_abstract_expected, meeting_abstract_expected / rows_processed))
print('Articles not in PubMed: {0} ({1}))'.format(article_not_in_pubmed,
    article_not_in_pubmed / rows_processed))
print('Meeting Abstract in PubMed: {0} ({1}))'.format(
    meeting_abstract_in_pubmed, meeting_abstract_in_pubmed / rows_processed))
