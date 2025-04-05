from django import template

register = template.Library()


@register.filter(name="get_item")
def get_item(dictionary, key):
    """
    Custom template filter to retrieve an item from a dictionary by key.

    Args:
        dictionary (dict): The dictionary from which to retrieve the item.
        key: The key of the item to retrieve.

    Returns:
        The value associated with the key in the dictionary, or None if the key does not exist.
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None


@register.filter(name="getattribute")
def getattribute(value, arg):
    """
    Custom template filter to retrieve an attribute from an object.

    Args:
        value: The object from which to retrieve the attribute.
        arg: The name of the attribute to retrieve.

    Returns:
        The attribute value if it exists and is not callable, or the callable itself if it is callable.
        Returns None if the attribute does not exist or an exception occurs.
    """
    try:
        attr = getattr(value, str(arg))
        if callable(attr):
            return attr
        return attr
    except AttributeError:
        return None
    except Exception:
        # In case of other errors
        return None
