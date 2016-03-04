from django import template
from django.conf import settings

register = template.Library()

# settings value
@register.simple_tag
def settings_value(name):
	defaults = {
		'SITE_HEADER': '<b>Map</b>Glass',
		'SITE_TITLE': 'MapGround'
	}
	if name in defaults:
		return getattr(settings, name, defaults[name])
	else:
		return ''