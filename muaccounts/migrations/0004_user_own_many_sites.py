
from south.db import db
from django.db import models
from muaccounts.models import *

class Migration:
    
    def forwards(self, orm):
        
        # Deleting unique_together for [owner] on muaccount.
        db.delete_unique('muaccounts_muaccount', ['owner_id'])
        
        # Changing field 'MUAccount.owner'
        # (to signature: django.db.models.fields.related.ForeignKey(blank=True, null=True, to=orm['auth.User']))
        db.alter_column('muaccounts_muaccount', 'owner_id', orm['muaccounts.muaccount:owner'])
        
    
    
    def backwards(self, orm):
        
        # Changing field 'MUAccount.owner'
        # (to signature: django.db.models.fields.related.OneToOneField(to=orm['auth.User'], unique=True, null=True, blank=True))
        db.alter_column('muaccounts_muaccount', 'owner_id', orm['muaccounts.muaccount:owner'])
        
        # Creating unique_together for [owner] on muaccount.
        db.create_unique('muaccounts_muaccount', ['owner_id'])
        
    
    
    models = {
        'auth.group': {
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'unique_together': "(('content_type', 'codename'),)"},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'unique_together': "(('app_label', 'model'),)", 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'muaccounts.muaccount': {
            'about': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'adsense_code': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'analytics_code': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'domain': ('django.db.models.fields.CharField', [], {'max_length': '256', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_public': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'blank': 'True'}),
            'logo': ('RemovableImageField', [], {'null': 'True', 'blank': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.User']", 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '256'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'owned_sites'", 'null': 'True', 'to': "orm['auth.User']"}),
            'subdomain': ('django.db.models.fields.CharField', [], {'max_length': '256', 'unique': 'True', 'null': 'True'}),
            'tag_line': ('django.db.models.fields.CharField', [], {'max_length': '256', 'blank': 'True'}),
            'theme': ('PickledObjectField', [], {'default': '( lambda :DEFAULT_THEME_DICT)'}),
            'webmaster_tools_code': ('django.db.models.fields.CharField', [], {'max_length': '150', 'blank': 'True'})
        }
    }
    
    complete_apps = ['muaccounts']
