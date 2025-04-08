import factory
from factory.django import DjangoModelFactory
from faker import Faker
import random

from .models.player import Player
from .models.sport_club import SportClub
from .models.category import Category
from .models.constants import AVAILABLE_DISCIPLINES

fake = Faker('pl_PL')


class SportClubFactory(DjangoModelFactory):
    class Meta:
        model = SportClub
        django_get_or_create = ('name',)  # Unikaj duplikatów klubów o tej samej nazwie

    name = factory.Faker('company', locale='pl_PL')  # Generuje nazwę firmy jako nazwę klubu


CATEGORY_NAMES = [
    "Najlepszy Ząbkowiczanin", "Najlepsza Ząbkowiczanka",
    "Junior do 16 roku życia", "Junior",
    "Pro Mężczyźni do 85 kg", "Pro Mężczyźni powyżej 85 kg", "Masters 45+",
    "Amator Kobiety do 65 kg", "Amator Kobiety powyżej 65 kg", "Amator Mężczyźni do 85 kg",
    "Amator Mężczyźni powyżej 85 kg",
    "Pro Kobiety do 65 kg", "Pro Kobiety powyżej 65 kg",
]


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category
        django_get_or_create = ('name',)  # Unikaj duplikatów kategorii

    name = factory.Iterator(CATEGORY_NAMES)

    @factory.lazy_attribute
    def disciplines(self):
        all_discipline_codes = [code for code, name in AVAILABLE_DISCIPLINES]
        k = random.randint(1, min(4, len(all_discipline_codes)))
        return random.sample(all_discipline_codes, k=k)


class PlayerFactory(DjangoModelFactory):
    class Meta:
        model = Player

    name = factory.Faker('first_name', locale='pl_PL')
    surname = factory.Faker('last_name', locale='pl_PL')
    weight = factory.Faker('pyfloat', left_digits=3, right_digits=1, positive=True, min_value=50.0, max_value=130.0)

    # Używa SubFactory do automatycznego tworzenia (lub pobierania) klubu
    club = factory.SubFactory(SportClubFactory)

    @factory.post_generation
    def categories(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for category in extracted:
                self.categories.add(category)
        else:
            try:
                all_categories = list(Category.objects.all())
                if all_categories:
                    num_categories = random.randint(1, min(2, len(all_categories)))  # Max 2 kategorie
                    random_categories = random.sample(all_categories, k=num_categories)
                    self.categories.add(*random_categories)
                else:
                    print("Warning: No categories found in DB. Creating some default ones for player.")
                    pass  # Lub po prostu nie przypisuj kategorii
            except Exception as e:
                print(f"Error adding categories to player {self.name} {self.surname}: {e}")
