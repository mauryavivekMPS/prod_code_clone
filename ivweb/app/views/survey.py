from django.http import HttpResponseRedirect, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render

SURVEYS = {
    'manager-nps-survey': 'https://www.surveymonkey.com/r/B52V9PD',
    'vizor-nps-survey': 'https://www.surveymonkey.com/r/VizorUserSurveyH9J8PGG',
}


@csrf_exempt
def redirect(request, survey_id):
    if survey_id in SURVEYS:
        return HttpResponseRedirect(SURVEYS[survey_id] + '?source=' + request.GET.get('source', 'unknown'))
    else:
        return HttpResponse('Unrecognized survey ID')


@csrf_exempt
def vizor_survey_link(request, survey_id):
    return render(request, 'survey/survey_link_for_vizors.html', {
        'survey_id': survey_id,
        'source': request.GET.get('source'),
    })
