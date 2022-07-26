from django import template

register = template.Library()


@register.filter
def prometheus_port(value):
    """Calculated port for the prometheus exporter"""
    return value + 10000 if value != 3306 else 9104
