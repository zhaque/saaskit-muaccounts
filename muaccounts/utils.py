
from django.conf import settings
from django.contrib.sites.models import Site
from django.utils.http import urlquote_plus
from django.core.urlresolvers import reverse
from django.contrib.auth import REDIRECT_FIELD_NAME

try:
    import sso
except ImportError:
    USE_SSO = False
else:
    USE_SSO = getattr(settings, 'MUACCOUNTS_USE_SSO', True)

def construct_main_site_url(location, sso_wraped=USE_SSO):
    port = (":%d" % settings.MAIN_SITE_PORT) \
            if hasattr(settings, 'MAIN_SITE_PORT') \
            else ''
    base_url = getattr(settings, 'MUACCOUNTS_DEFAULT_URL', 
                       "http://%s%s" % (Site.objects.get_current().domain, port))
    url = "%s%s" % (base_url, location[1:] if location.startswith('/') else location)
    
    return sso_wrap(url) if sso_wraped else url 

def sso_wrap(url):
    return "%s?%s=%s" % (reverse('sso'), REDIRECT_FIELD_NAME, urlquote_plus(url))
