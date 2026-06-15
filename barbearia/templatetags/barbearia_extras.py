from django import template

register = template.Library()


@register.filter(name='lookup')
def lookup(obj, key):
    """Allow {{ form|lookup:campo }} to get a form field by variable name."""
    try:
        return obj[key]
    except (KeyError, TypeError):
        return ''
