from django import template
from django.conf import settings
from django.template import TemplateSyntaxError
from django.utils.encoding import smart_str

from muaccounts.utils import construct_main_site_url, sso_wrap, USE_SSO

register = template.Library()


class SitesListNode(template.Node):

    def __init__(self, user, var_name, rel):
        self.user = template.Variable(user)
        self.var_name = var_name
        self.rel = rel

    def render(self, context):
        user = self.user.resolve(context)
        context[self.var_name] = getattr(user, self.rel).all()
        return ''


def sites_list(parser, token, rel):
    bits = token.split_contents()
    if not len(bits) == 4:
        raise template.TemplateSyntaxError,\
              "%r's format is {% %s user as var %}" % (bits[0], bits[0])
    return SitesListNode(user=bits[1], var_name=bits[3], rel=rel)


@register.tag
def sites_owned(parser, token):
    return sites_list(parser, token, 'owned_sites')


@register.tag
def member_of(parser, token):
    return sites_list(parser, token, 'muaccount_member')


@register.tag
def main_site_url(parser, token):
    res = template.defaulttags.url(parser, token)
    if isinstance(res, template.defaulttags.URLNode):
        return MainURLNode(res.view_name, res.args, res.kwargs, res.asvar)
    else:
        return res

class MainURLNode(template.defaulttags.URLNode):
    
    def render(self, context):
        """ copy of default tag URLNode render method. Just url_conf was changed """ 
        from django.core.urlresolvers import reverse, NoReverseMatch
        args = [arg.resolve(context) for arg in self.args]
        kwargs = dict([(smart_str(k,'ascii'), v.resolve(context))
                       for k, v in self.kwargs.items()])

        # Try to look up the URL twice: once given the view name, and again
        # relative to what we guess is the "main" app. If they both fail,
        # re-raise the NoReverseMatch unless we're using the
        # {% url ... as var %} construct in which cause return nothing.
        url = ''
        try:
            url = reverse(self.view_name, urlconf=settings.MUACCOUNTS_MAIN_URLCONF, 
                          args=args, kwargs=kwargs, current_app=context.current_app)
        except NoReverseMatch, e:
            if settings.SETTINGS_MODULE:
                project_name = settings.SETTINGS_MODULE.split('.')[0]
                try:
                    url = reverse(project_name + '.' + self.view_name, 
                                  urlconf=settings.MUACCOUNTS_MAIN_URLCONF,
                                  args=args, kwargs=kwargs, current_app=context.current_app)
                except NoReverseMatch:
                    if self.asvar is None:
                        # Re-raise the original exception, not the one with
                        # the path relative to the project. This makes a
                        # better error message.
                        raise e
            else:
                if self.asvar is None:
                    raise e
        
        url  = construct_main_site_url(url)
        
        if self.asvar:
            context[self.asvar] = url
            return ''
        else:
            return url


@register.tag
def user_site_url(parser, token):
    """ alomost copy of default tag url. just added muaccount parameter """
    bits = token.split_contents()
    if len(bits) < 3:
        raise TemplateSyntaxError("'%s' takes at least two arguments"
                                  " (path to a view and muaccount)" % bits[0])
    viewname = bits[1]
    muaccount = parser.compile_filter(bits[2])
    args = []
    kwargs = {}
    asvar = None

    if len(bits) > 3:
        bits = iter(bits[3:])
        for bit in bits:
            if bit == 'as':
                asvar = bits.next()
                break
            else:
                for arg in bit.split(","):
                    if '=' in arg:
                        k, v = arg.split('=', 1)
                        k = k.strip()
                        kwargs[k] = parser.compile_filter(v)
                    elif arg:
                        args.append(parser.compile_filter(arg))
    return UserSiteURLNode(muaccount, viewname, args, kwargs, asvar)
    
class UserSiteURLNode(template.defaulttags.URLNode):
    
    def __init__(self, muaccount, *args, **kwargs):
        super(UserSiteURLNode, self).__init__(*args, **kwargs)
        self.muaccount = muaccount
    
    def render(self, context):
        args = [arg.resolve(context) for arg in self.args]
        kwargs = dict([(smart_str(k,'ascii'), v.resolve(context))
                       for k, v in self.kwargs.items()])
        
        muaccount = self.muaccount.resolve(context)
        
        url = muaccount.get_absolute_url(self.view_name, args, kwargs)
        url = sso_wrap(url) if USE_SSO else url 
        
        if self.asvar:
            context[self.asvar] = url
            return ''
        else:
            return url
