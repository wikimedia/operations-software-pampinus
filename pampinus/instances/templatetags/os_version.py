from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
@stringfilter
def os_alias(value):
    """Calculated port for the prometheus exporter"""
    alias = {13: 'trixie',
             12: 'bookworm',
             11: 'bullseye',
             10: 'buster',
             9: 'stretch',
             8: 'jessie'}
    try:
        major_version = int(value.split('.')[0])
    except ValueError:
        return None
    if major_version not in alias.keys():
        return None
    else:
        return alias[major_version]
