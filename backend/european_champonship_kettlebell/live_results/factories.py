import factory
from factory.django import DjangoModelFactory
from faker import Faker
import random

# Załóżmy, że modele są w live_results.models lub live_results.models.nazwa_pliku
# Dostosuj ścieżki importu do swojej struktury projektu
from .models.player import Player
from .models.sport_club import SportClub
from .models.category import Category
# Załóżmy, że masz zdefiniowane stałe z dyscyplinami gdzieś, np. w constants
from .models.constants import SNATCH,SEE_SAW_PRESS,KB_SQUAT,TGU,PISTOL_SQUAT,ONE_KB_PRESS,TWO_KB_PRESS
from .models.constants import AVAILABLE_DISCIPLINES
# Utwórz instancję Fakera (można ustawić polski locale dla bardziej polskich danych)
fake = Faker('pl_PL')

# --- Fabryka dla Klubu Sportowego ---
class SportClubFactory(DjangoModelFactory):
    class Meta:
        model = SportClub
        django_get_or_create = ('name',) # Unikaj duplikatów klubów o tej samej nazwie

    name = factory.Faker('company', locale='pl_PL') # Generuje nazwę firmy jako nazwę klubu

# --- Fabryka dla Kategorii ---
# Lista przykładowych, realistycznych nazw kategorii
CATEGORY_NAMES = [
    "Junior Kobiety U18", "Junior Mężczyźni U18",
    "Senior Kobiety Open", "Senior Mężczyźni Open",
    "Masters Kobiety 40+", "Masters Mężczyźni 40+", "Masters Mężczyźni 50+",
    "Weteran Kobiety 60+", "Weteran Mężczyźni 60+",
    "Pro Kobiety", "Pro Mężczyźni"
]

class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category
        django_get_or_create = ('name',) # Unikaj duplikatów kategorii

    name = factory.Iterator(CATEGORY_NAMES)

    # Jeśli Twoja kategoria ma pole 'disciplines' (jak sugeruje admin.py)
    # Możesz dodać logikę do jego wypełniania, np.:
    # @factory.lazy_attribute
    # def disciplines(self):
    #     # Zakładając, że AVAILABLE_DISCIPLINES to lista krotek np. [('SN', 'Snatch'), ...]
    #     all_discipline_codes = [code for code, name in AVAILABLE_DISCIPLINES]
    #     # Wybierz losowo od 1 do 4 dyscyplin dla kategorii
    #     k = random.randint(1, min(4, len(all_discipline_codes)))
    #     return random.sample(all_discipline_codes, k=k)

# --- Fabryka dla Zawodnika ---
class PlayerFactory(DjangoModelFactory):
    class Meta:
        model = Player

    name = factory.Faker('first_name', locale='pl_PL')
    surname = factory.Faker('last_name', locale='pl_PL')
    # Generuje wagę jako liczbę zmiennoprzecinkową (jeśli DecimalField, użyj pydecimal)
    # Dostosuj zakres (min_value, max_value) i precyzję (right_digits)
    weight = factory.Faker('pyfloat', left_digits=3, right_digits=1, positive=True, min_value=50.0, max_value=130.0)

    # Używa SubFactory do automatycznego tworzenia (lub pobierania) klubu
    club = factory.SubFactory(SportClubFactory)

    # Pole `categories` jest ManyToManyField - obsługujemy je po wygenerowaniu obiektu
    @factory.post_generation
    def categories(self, create, extracted, **kwargs):
        if not create:
            # Prosta obsługa: nic nie rób, jeśli tylko budujemy obiekt (nie zapisujemy do DB)
            return

        if extracted:
            # Jeśli kategorie zostały przekazane jawnie: PlayerFactory(categories=(cat1, cat2))
            for category in extracted:
                self.categories.add(category)
        else:
            # Domyślna logika: przypisz 1 lub 2 losowe, istniejące kategorie
            # Upewnij się, że kategorie istnieją w bazie przed generowaniem zawodników!
            try:
                all_categories = list(Category.objects.all())
                if all_categories:
                    num_categories = random.randint(1, min(2, len(all_categories))) # Max 2 kategorie
                    random_categories = random.sample(all_categories, k=num_categories)
                    self.categories.add(*random_categories)
                else:
                    # Opcjonalnie: stwórz kategorie, jeśli żadne nie istnieją
                    print("Warning: No categories found in DB. Creating some default ones for player.")
                    # default_cats = CategoryFactory.create_batch(2)
                    # self.categories.add(*default_cats)
                    pass # Lub po prostu nie przypisuj kategorii
            except Exception as e:
                print(f"Error adding categories to player {self.name} {self.surname}: {e}")


    # Jeśli masz inne pola, np. 'tiebreak', dodaj je tutaj
    # Zakładając, że tiebreak to FloatField (na podstawie admin.py)
    # tiebreak = factory.Faker('pyfloat', left_digits=1, right_digits=2, positive=True, min_value=0.0, max_value=5.0)
    # Jeśli BooleanField:
    # tiebreak = factory.Faker('boolean', chance_of_getting_true=25)