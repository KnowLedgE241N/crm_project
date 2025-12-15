from django import template

register = template.Library()

@register.filter
def get_attr(obj, attr):
    return getattr(obj, attr)

@register.filter
def get_item(obj, key):
    """
    Supports:
    - Django forms: form["field_name"]
    - dicts: d.get("key")
    - any object with __getitem__
    """
    try:
        return obj[key]  # Django forms work like this
    except Exception:
        try:
            return obj.get(key)  # dict-like fallback
        except Exception:
            return None
