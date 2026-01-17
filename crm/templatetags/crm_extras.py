from django import template

register = template.Library()

@register.filter
def get_attr(obj, attr_name):
    """
    Usage: {{ obj|get_attr:"field_name" }}
    Safe fallback to empty string if missing.
    """
    if obj is None or not attr_name:
        return ""
    return getattr(obj, attr_name, "")
