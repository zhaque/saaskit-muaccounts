from django.http import HttpResponseForbidden


def owner_only(func):

    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated() or \
                not (request.muaccount.owner == request.user):
            return HttpResponseForbidden()
        return func(request, *args, **kwargs)

    return wrapped

def public(func):
    """ decorator that give access right even if user site is not public."""
    def wrapper(request, *args, **kwargs):
        return func(request, *args, **kwargs)
    wrapper.is_public = True
    
    return wrapper
