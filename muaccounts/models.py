import warnings

from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _

from muaccounts import signals
from muaccounts.model_fields import RemovableImageField, PickledObjectField
from muaccounts.themes import DEFAULT_THEME_DICT

def _subdomain_root():
    root = settings.MUACCOUNTS_ROOT_DOMAIN
    if not root.startswith('.'):
        root = '.'+root
    return root

#_muaccount_logo_path = lambda instance, filename: 'muaccount-logos/%d.jpg' % instance.pk

class MUAccount(models.Model):
    owner = models.ForeignKey(User, verbose_name=_('Owner'), related_name='owned_sites',
                              null=True, blank=True)
    members = models.ManyToManyField(User, related_name='muaccount_member', blank=True, verbose_name=_('Members'))
    name = models.CharField(max_length=256, verbose_name=_('Name'))
    tag_line = models.CharField(max_length=256, blank=True)
    about = models.TextField(blank=True)
    logo = RemovableImageField(upload_to=lambda instance, filename: 'muaccount-logos/%d.jpg' % instance.pk, 
                               null=True, blank=True)
    domain = models.CharField(max_length=256, unique=True, verbose_name=_('Domain'), blank=True, null=True)
    subdomain = models.CharField(max_length=256, unique=True, verbose_name=_('Subdomain'), null=True)
    is_public = models.BooleanField(default=True, verbose_name=_('Is public'))
    theme = PickledObjectField(default=(lambda : DEFAULT_THEME_DICT), verbose_name=_('Theme')) # lambda to work around http://code.djangoproject.com/ticket/8633

    analytics_code = models.TextField(blank=True)
    webmaster_tools_code = models.CharField(max_length=150, blank=True)
    adsense_code = models.TextField(blank=True)
    
    yahoo_app_id = models.CharField(_("yahoo application ID"), max_length=150, blank=True)
    yahoo_secret = models.CharField(_("yahoo shared secret"), max_length=150, blank=True)

    subdomain_root = _subdomain_root()

    class Meta:
        permissions = (
            ('can_set_custom_domain', 'Can set custom domain'),
            ('can_set_public_status', 'Can set public status'),
            ('can_set_adsense_code', 'Can set AdSense code'),
        )

    def __unicode__(self):
        return self.name or self.domain or self.subdomain+self.subdomain_root

    def get_full_domain(self):
        return self.domain or self.subdomain+self.subdomain_root

    def get_absolute_url(self, path='/', args=(), kwargs={}):
        if hasattr(settings, 'MUACCOUNTS_PORT'): port=':%d'%settings.MUACCOUNTS_PORT
        else: port = ''
        if not path.startswith('/'):
            if hasattr(settings, 'MUACCOUNTS_USERSITE_URLCONF'):
                path = reverse(path, args=args, kwargs=kwargs,
                               urlconf=settings.MUACCOUNTS_USERSITE_URLCONF)
            else:
                warnings.warn(
                    'Cannot resolve without settings.MUACCOUNTS_USERSITE_URLCONF, using / path.')
                path = '/'
        return 'http://%s%s%s' % (self.get_full_domain(), port, path)

    def add_member(self, user):
        self.members.add(user)
        signals.add_member.send(self, user=user)

    def remove_member(self, user):
        self.members.remove(user)
        signals.remove_member.send(self, user=user)

class JoinRequest(models.Model):
    
    STATE_INIT = 1
    STATE_JOINED = 2
    STATE_REJECTED = 3
    
    STATE_CHOICES = (
        (STATE_INIT, _("waiting")),
        (STATE_JOINED, _("member was added")),
        (STATE_REJECTED, _("Owner rejected request")),
    )
    
    user = models.ForeignKey(User, related_name="join_requests")
    muaccount = models.ForeignKey(MUAccount, related_name="join_requests")
    notes = models.TextField(_("notes"), blank=True)
    state = models.IntegerField(_('state'), choices=STATE_CHOICES, default=STATE_INIT, editable=False)
    created = models.DateTimeField(auto_now=True, editable=False)
    
    class Meta:
        verbose_name = _('join request')
        verbose_name_plural = _('join requests')
        unique_together = (('user', 'muaccount'),)
        ordering = ('-created',)
    
    def join(self):
        if self.state == self.STATE_INIT:
            self.muaccount.add_member(self.user)
            self.state = self.STATE_JOINED
            self.save()
        else:
            raise ValueError("Only just initialized request can be accepted.")
    
    def reject(self):
        if self.state == self.STATE_INIT:
            self.state = self.STATE_REJECTED
            self.save()
        else:
            raise ValueError("Only just initialized request can be rejected.")
        