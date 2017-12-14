from django.http import HttpResponseRedirect, HttpResponse

SURVEYS = {
    'manager-nps-survey': 'https://www.surveymonkey.com/r/B52V9PD',
    'vizor-nps-survey': 'https://www.surveymonkey.com/r/VizorUserSurveyH9J8PGG',
}


def redirect(request, survey_id):
    if survey_id in SURVEYS:
        return HttpResponseRedirect(SURVEYS[survey_id] + '?source=' + request.GET.get('source', 'unknown'))
    else:
        return HttpResponse('Unrecognized survey ID')
