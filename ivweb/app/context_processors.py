from ivetl import common
from ivweb.app import constants as ivweb_constants


def common(request):
    return {'common': common}


def constants(request):
    return {
        'constants': ivweb_constants
    }
