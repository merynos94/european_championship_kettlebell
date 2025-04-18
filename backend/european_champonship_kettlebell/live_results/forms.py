from django import forms
from .models import Category

class StationForm(forms.Form):
    categories = forms.MultipleChoiceField(
        choices=[], 
        label="Kategorie",
        widget=forms.CheckboxSelectMultiple(),
        help_text="Wybierz jedną lub więcej kategorii do połączenia"
    )
    stations = forms.IntegerField(
        min_value=1, 
        label="Liczba stanowisk",
        help_text="Wprowadź liczbę dostępnych stanowisk"
    )
    distribute_evenly = forms.BooleanField(
        required=False, 
        initial=True,
        label="Rozdziel równomiernie",
        help_text="Zaznacz, aby rozdzielić zawodników równomiernie między stanowiska"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["categories"].choices = [
            (category.name, category.name.replace("_", " "))
            for category in Category.objects.all()
        ]