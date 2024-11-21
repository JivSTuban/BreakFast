from django import template

register = template.Library()

@register.filter(name='multiply')
def multiply(value, arg):
    """Multiply the value by the argument"""
    try:
        value = float(value)
        arg = float(arg)
        result = value * arg
        return '{:.2f}'.format(result)  # Format to 2 decimal places
    except (ValueError, TypeError):
        return 0
