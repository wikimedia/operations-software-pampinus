from django import template
from django.template.defaultfilters import filesizeformat

register = template.Library()


@register.filter
def percentage_change(value):
    """Print a size percentage change"""
    try:
        if float(value) >= 0:
            sign = '+'
        else:
            sign = '-'
        return f'{sign}{abs(round(value, 1)):.1f} %'  # in this house we observe ISO 31-0 standard
    except (ValueError, TypeError):
        return value


@register.filter
def bytes_change(value):
    """Print a size percentage change"""
    try:
        if int(value) >= 0:
            sign = '+'
        else:
            sign = '-'
        return f'{sign}{filesizeformat(abs(value))}'
    except (ValueError, TypeError):
        return value
