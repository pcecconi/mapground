from django import template
from django.conf import settings
from django.utils.safestring import mark_safe

register = template.Library()


# settings value
@register.simple_tag
def settings_value(name):
    defaults = {
        'SITE_HEADER': '<b>Map</b>Ground',
        'SITE_TITLE': 'MapGround'
    }
    if name in defaults:
        return mark_safe(getattr(settings, name, defaults[name]))
    else:
        return ''
