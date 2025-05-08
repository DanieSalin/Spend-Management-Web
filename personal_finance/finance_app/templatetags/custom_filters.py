from django import template

register = template.Library()

@register.filter
def subtract(value, arg):
    """Trừ arg từ value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, total):
    """Tính phần trăm của value so với total"""
    try:
        if float(total) == 0:
            return 0
        return round((float(value) / float(total)) * 100, 1)
    except (ValueError, TypeError):
        return 0 