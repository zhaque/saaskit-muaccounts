from django.conf import settings
from django.contrib.auth import logout
from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.utils.cache import patch_vary_headers
from django.contrib.auth.views import redirect_to_login
from django.utils.translation import ugettext, ugettext_lazy as _

from models import MUAccount
import signals

class MUAccountsMiddleware(object):
    def __init__(self):

        if hasattr(settings, 'MUACCOUNTS_PORT'):
            self.port_suffix = ':%d' % settings.MUACCOUNTS_PORT
        else: self.port_suffix = ''

        self.default_domain = getattr(settings, 'MUACCOUNTS_DEFAULT_DOMAIN', None)
        self.default_url = getattr(settings, 'MUACCOUNTS_DEFAULT_URL',
                                   'http://%s%s/' % (
                                       self.default_domain or Site.objects.get_current().domain,
                                       self.port_suffix ))

    def process_request(self, request):
        host = request.get_host()

        # strip port suffix if present
        if self.port_suffix and host.endswith(self.port_suffix):
            host = host[:-len(self.port_suffix)]

        try:
            if host.endswith(MUAccount.subdomain_root):
                mua = MUAccount.objects.get(
                    subdomain=host[:-len(MUAccount.subdomain_root)])
                if mua.domain:
                    return redirect(mua.get_absolute_url())
            else:
                mua = MUAccount.objects.get(domain=host)
        except MUAccount.DoesNotExist:
            if host <> self.default_domain:
                return HttpResponseRedirect(self.default_url)
        else:
            # set up request parameters
            request.muaccount = mua
            
    def process_view(self, request, view, args, kwargs):
        
        #check whether request has muaccount attribute
        #check whether request for media files
        #check special anchor is_public
        if not hasattr(request, 'muaccount') \
        or request.path.startswith(settings.MEDIA_URL) \
        or getattr(view, 'is_public', False):
            return 
        
        #redirect user to log in if account is not public
        #this check should be in distinct middleware i think
        #as it depends on django_authopenid for example
        if not request.muaccount.is_public \
        and not request.user.is_authenticated() :
            return redirect_to_login(request.get_full_path())
        
        # force logout of non-member and non-owner from non-public site
        if request.user.is_authenticated() \
               and request.user != request.muaccount.owner \
               and  not request.muaccount.members.filter(username=request.user.username).count():
            
            if request.muaccount.is_public or request.muaccount.owner is None:
                request.muaccount.add_member(request.user)
                request.user.message_set.create(message=ugettext("You was added to this site successfully."))
            else:
                return redirect(reverse('join_request'))
        
        # call request hook
        for receiver, retval in signals.muaccount_request.send(sender=request, 
                                    request=request, muaccount=request.muaccount):
            if isinstance(retval, HttpResponse):
                return retval


    def process_response(self, request, response):
        if getattr(request, "urlconf", None):
            patch_vary_headers(response, ('Host',))
        return response
