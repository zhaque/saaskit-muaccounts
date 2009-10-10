from django import template

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
