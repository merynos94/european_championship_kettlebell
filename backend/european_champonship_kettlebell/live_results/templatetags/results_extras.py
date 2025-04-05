# live_results/templatetags/results_extras.py
from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Umożliwia dostęp do elementu słownika za pomocą zmiennej klucza w szablonach Django.
    Użycie: {{ my_dictionary|get_item:my_key_variable }}
    Zwraca None, jeśli klucz nie istnieje.
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter(name='getattribute')
def getattribute(value, arg):
    """
    Umożliwia dostęp do atrybutu obiektu za pomocą zmiennej nazwy atrybutu.
    Użycie: {{ my_object|getattribute:my_attribute_name_variable }}
    Zwraca None, jeśli atrybut nie istnieje lub wystąpi błąd.
    """
    try:
        attr = getattr(value, str(arg))
        if callable(attr):
            # Nie wywołuj metod, zwróć samą metodę lub None/pusty string?
            # Zazwyczaj chcemy wartość, więc jeśli jest to np. property, to jest OK.
            # Jeśli to prawdziwa metoda wymagająca argumentów, to nie zadziała.
            # Dla bezpieczeństwa, można by zwrócić '' lub None dla callable.
            # return ''
            return attr # Zwraca wartość property lub samą metodę
        return attr
    except AttributeError:
        return None
    except Exception:
        # W razie innych błędów
        return None