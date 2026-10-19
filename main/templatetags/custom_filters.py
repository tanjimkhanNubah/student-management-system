# main/templatetags/custom_filters.py

from django import template

register = template.Library()

@register.filter
def split(value, arg):
    """Splits a string by the argument (arg) and returns a list."""
    return value.split(arg)

# ✅ নতুন যোগ করা হলো: strip filter
@register.filter
def strip(value):
    """Removes leading and trailing whitespace from a string."""
    return value.strip()