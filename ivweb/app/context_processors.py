from ivetl.common import common as ivetl_common
from ivweb.app import constants as ivweb_constants


def common(request):
    return {'common': ivetl_common}


def constants(request):
    return {'constants': ivweb_constants}
