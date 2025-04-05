from django.core.management.base import BaseCommand
from django.db import transaction
import random

# Importuj modele, jeśli potrzebujesz bezpośredniego dostępu
from ...factories import PlayerFactory, SportClubFactory, CategoryFactory, CATEGORY_NAMES
from ...models import SportClub, Category, Player


class Command(BaseCommand):
    help = 'Populates the database with sample player data using Factory Boy.'

    # Możesz dodać argumenty, np. liczbę zawodników do stworzenia
    def add_arguments(self, parser):
        parser.add_argument(
            '--number',
            type=int,
            help='Number of players to create',
            default=300 # Domyślna liczba zawodników
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing Players, Categories, and SportClubs before populating',
        )

    @transaction.atomic # Uruchom wszystko w jednej transakcji
    def handle(self, *args, **options):
        num_players = options['number']
        clear_data = options['clear']

        if clear_data:
            self.stdout.write(self.style.WARNING('Clearing existing Player, Category, and SportClub data...'))
            Player.objects.all().delete()
            Category.objects.all().delete()
            SportClub.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Data cleared.'))


        self.stdout.write("Populating database with sample data...")

        # --- 1. Stwórz Kluby Sportowe ---
        # Stwórz określoną liczbę klubów lub upewnij się, że jakieś istnieją
        num_clubs = 25
        # SportClubFactory.create_batch(num_clubs) # Tworzy DOKŁADNIE tyle nowych klubów
        # Lepsze podejście: stwórz tylko jeśli potrzeba, unikaj duplikatów dzięki django_get_or_create
        clubs = [SportClubFactory() for _ in range(num_clubs)]
        self.stdout.write(f"Ensured at least {len(SportClub.objects.all())} Sport Clubs exist.")

        # --- 2. Stwórz Kategorie ---
        # Używamy Iteratora w fabryce, więc create_batch stworzy kategorie z listy CATEGORY_NAMES
        # CategoryFactory.create_batch(len(CATEGORY_NAMES))
        # Lepsze podejście z django_get_or_create:
        categories = [CategoryFactory() for _ in range(len(CATEGORY_NAMES))] # Stworzy/pobierze kategorie z listy
        self.stdout.write(f"Ensured {len(Category.objects.all())} Categories exist.")

        # Sprawdzenie, czy kategorie na pewno istnieją przed tworzeniem zawodników
        if not Category.objects.exists():
             self.stderr.write(self.style.ERROR("No categories found or created. Cannot assign categories to players."))
             return # Zakończ, jeśli nie ma kategorii

        # --- 3. Stwórz Zawodników ---
        # Użyj create_batch dla wydajności
        self.stdout.write(f"Creating {num_players} players...")
        players = PlayerFactory.create_batch(num_players)
        self.stdout.write(self.style.SUCCESS(f"Successfully created {len(players)} players."))

        self.stdout.write(self.style.SUCCESS("Database population complete."))