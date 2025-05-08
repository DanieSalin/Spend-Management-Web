from django import template

register = template.Library()

@register.filter
def subtract(value, arg):
    """Trừ hai số"""
    try:
        return value - arg
    except (ValueError, TypeError):
        return 0 