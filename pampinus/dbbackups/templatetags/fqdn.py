from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
@stringfilter
def datacenter(value):
    """Calculat the wmf datacenter from a given fqdn"""
    return value.split('.')[1]


@register.filter
@stringfilter
def fqdn_to_instance(value):
    """Calculate the wmf datacenter from a given fqdn"""
    identifier = value.split(':')
    if len(identifier) == 1 or identifier[1] == 3306:
        return identifier[0].split('.')[0]
    else:
        return identifier[0].split('.')[0] + ':' + identifier[1]
