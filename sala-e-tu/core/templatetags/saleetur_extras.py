from django import template

register = template.Library()


@register.filter
def brl(value):
    try:
        value = float(value)
        formatted = f"{value:,.2f}"
        return formatted.replace(',', 'X').replace('.', ',').replace('X', '.')
    except (ValueError, TypeError):
        return value
