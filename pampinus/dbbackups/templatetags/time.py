from django import template

register = template.Library()


@register.filter
def seconds(value):
    """Print a given timestamp duration in seconds"""
    if value is None:
        return None
    return int(value.total_seconds())


@register.filter
def timespan(value):
    """Print a timestamp duration in a human readable format"""
    if value is None:
        return None
    seconds = int(value.total_seconds())
    if seconds < 60:
        return str(seconds) + 's'
    minutes = (seconds // 60)
    seconds = seconds - (minutes * 60)
    if minutes < 60:
        return str(minutes) + 'm ' + str(seconds) + 's'
    hours = (minutes // 60)
    minutes = minutes - (hours * 60)
    return str(hours) + 'h ' + str(minutes) + 'm'
