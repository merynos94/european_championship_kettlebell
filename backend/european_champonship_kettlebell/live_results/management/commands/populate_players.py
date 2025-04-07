import random
import csv
import os
import traceback  # Dodaj import traceback na wszelki wypadek

from django.core.management.base import BaseCommand
from django.db import transaction

# Importuj modele i fabryki
from ...factories import PlayerFactory, SportClubFactory, CategoryFactory, CATEGORY_NAMES
from ...models import SportClub, Category, Player


class Command(BaseCommand):
    help = 'Populates the database with sample player data using Factory Boy and exports to CSV.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--number',
            type=int,
            help='Number of players to generate',
            default=0
        )
        parser.add_argument(
            '--clubs',
            type=int,
            help='Target number of sport clubs to ensure exist',
            default=10
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing Players (keeps Categories and SportClubs)',
        )
        parser.add_argument(
            '--exporttofile',
            action='store_true',
            help='Generate and export players to CSV file (default: fake_zawodnicy.csv)',
        )
        parser.add_argument(
            '--addtodb',
            action='store_true',
            help='Add generated players to the database (if --number > 0)',
        )
        parser.add_argument(
            '--export-path',
            type=str,
            help='Path where to save CSV file (default: current directory)',
            default='.'
        )

    def export_players_to_csv(self, players, export_path):
        """Export players data to a CSV file."""
        filepath = os.path.join(export_path, 'fake_zawodnicy.csv')
        os.makedirs(export_path, exist_ok=True)
        self.stdout.write(f"Exporting data to {filepath}...")

        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            # Zgodnie z PlayerImportResource, używamy tych kolumn
            fieldnames = ['id', 'name', 'surname', 'club', 'categories']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for idx, player in enumerate(players, 1):
                # Dla graczy w pamięci bez ID z bazy, użyj numeru sekwencyjnego
                # Jeśli gracz ma pk (z bazy), użyj go, inaczej zostaw puste (import sam nada ID)
                player_id = getattr(player, 'pk', '')  # Użyj pk jeśli istnieje, inaczej puste dla nowych

                # Pobierz kategorie
                player_categories = []
                if hasattr(player, '_categories'):
                    # Dla obiektów w pamięci stworzonych przez .build()
                    player_categories = player._categories
                elif hasattr(player, 'pk') and player.pk:
                    # Dla obiektów z bazy danych (mających pk)
                    # Użyj prefetch_related jeśli eksportujesz wielu graczy z DB
                    try:
                        player_categories = list(player.categories.all())
                    except Exception as e:
                        self.stderr.write(f"Error getting categories for player {player}: {e}")
                        player_categories = []

                # Formatuj nazwy kategorii na string rozdzielany przecinkami (bez spacji!)
                categories_str = ','.join(sorted([cat.name for cat in player_categories]))

                # Pobierz nazwę klubu
                club_name = ''
                if hasattr(player, 'club') and player.club:
                    if hasattr(player.club, 'name'):
                        club_name = player.club.name
                    else:  # Na wypadek gdyby club był tylko ID lub czymś innym
                        try:
                            club_obj = SportClub.objects.get(pk=player.club.pk)
                            club_name = club_obj.name
                        except SportClub.DoesNotExist:
                            club_name = f"Club PK {player.club.pk}"  # fallback
                        except AttributeError:
                            club_name = "Invalid Club Ref"

                writer.writerow({
                    'id': player_id,
                    'name': getattr(player, 'name', ''),
                    'surname': getattr(player, 'surname', ''),
                    'club': club_name,
                    'categories': categories_str
                })

        return filepath

    def generate_players(self, num_players, clubs, categories):
        """Generate players in memory without saving to database"""
        self.stdout.write(f"Generating {num_players} players in memory...")
        players = []
        if not categories:
            self.stderr.write(self.style.ERROR("No categories available to assign."))
            return []
        if not clubs:
            self.stderr.write(self.style.ERROR("No clubs available to assign."))
            return []

        for i in range(num_players):
            if not clubs:  # Dodatkowe zabezpieczenie
                self.stderr.write(self.style.WARNING("No more clubs available"))
                break
            club = random.choice(clubs)

            # Stwórz gracza w pamięci
            player = PlayerFactory.build(club=club)  # weight=None jest domyślne w fabryce? Jeśli nie, dodaj.

            # Przypisz 1 do 3 losowych, unikalnych kategorii (jeśli są dostępne)
            num_cats_to_assign = random.randint(1, min(3, len(categories)))
            assigned_categories = random.sample(categories, num_cats_to_assign)

            # Zapisz przypisane kategorie w atrybucie tymczasowym
            player._categories = assigned_categories

            # Dodaj ID sekwencyjne dla celów eksportu, jeśli nie ma pk
            if not hasattr(player, 'pk'):
                setattr(player, 'temp_id_for_export', i + 1)

            players.append(player)
        return players

    @transaction.atomic
    def handle(self, *args, **options):
        num_players_to_generate = options['number']
        num_clubs_target = options['clubs']
        clear_players = options['clear']
        export_to_file = options['exporttofile']
        add_to_db = options['addtodb']
        export_path = options['export_path']

        # Czyszczenie graczy (jeśli wymagane)
        if clear_players:
            self.stdout.write(self.style.WARNING('Clearing existing Player data...'))
            Player.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Player data cleared.'))

        # --- Zapewnij istnienie Klubów i Kategorii ---
        # Kluby
        existing_clubs = list(SportClub.objects.all())
        if len(existing_clubs) < num_clubs_target:
            clubs_to_create = num_clubs_target - len(existing_clubs)
            SportClubFactory.create_batch(clubs_to_create)
            self.stdout.write(f"Created {clubs_to_create} new Sport Clubs.")
            clubs = list(SportClub.objects.all())
        elif len(existing_clubs) > num_clubs_target:
            self.stdout.write(f"Using first {num_clubs_target} of {len(existing_clubs)} existing Sport Clubs.")
            clubs = existing_clubs[:num_clubs_target]
        else:
            self.stdout.write(f"Using {len(existing_clubs)} existing Sport Clubs.")
            clubs = existing_clubs

        if not clubs:
            self.stderr.write(self.style.ERROR("No Sport Clubs available. Cannot proceed."))
            return

        # Kategorie (zakładamy, że CATEGORY_NAMES są zdefiniowane w factories.py)
        existing_categories = list(Category.objects.all())
        if not existing_categories:
            # Jeśli nie ma żadnych kategorii, stwórz je na podstawie CATEGORY_NAMES
            if CATEGORY_NAMES:
                CategoryFactory.create_batch(len(CATEGORY_NAMES))
                self.stdout.write(f"Created {len(CATEGORY_NAMES)} Categories based on CATEGORY_NAMES.")
                categories = list(Category.objects.all())
            else:
                self.stderr.write(
                    self.style.ERROR("No categories found and CATEGORY_NAMES is empty. Cannot create categories."))
                categories = []
        else:
            self.stdout.write(f"Using {len(existing_categories)} existing Categories.")
            categories = existing_categories

        if not categories:
            self.stderr.write(self.style.ERROR("No Categories available. Cannot assign categories to players."))
            # Można rozważyć przerwanie, jeśli kategorie są absolutnie wymagane
            # return

        # --- Generowanie i/lub Eksport ---
        generated_players = []

        # 1. Generowanie i dodawanie do bazy danych
        if num_players_to_generate > 0 and add_to_db:
            self.stdout.write(f"Creating {num_players_to_generate} players and adding to database...")
            if not categories:
                self.stderr.write(self.style.ERROR("Cannot add players to DB: No categories available to assign."))
            else:
                for _ in range(num_players_to_generate):
                    if not clubs: break  # Zabezpieczenie
                    club = random.choice(clubs)

                    # Stwórz i zapisz gracza w DB
                    player = PlayerFactory(club=club)  # Użyj () zamiast .build() aby zapisać

                    # Przypisz 1 do 3 losowych, unikalnych kategorii (jeśli są dostępne)
                    num_cats_to_assign = random.randint(1, min(3, len(categories)))
                    assigned_categories = random.sample(categories, num_cats_to_assign)

                    # Użyj .set() do przypisania relacji ManyToMany dla zapisanego obiektu
                    player.categories.set(assigned_categories)

                    generated_players.append(player)  # Dodaj do listy graczy z tej sesji

            self.stdout.write(
                self.style.SUCCESS(f"Successfully created and saved {len(generated_players)} players to database."))

            # Jeśli dodano do DB i jednocześnie zażądano eksportu
            if export_to_file:
                if generated_players:
                    filepath = self.export_players_to_csv(generated_players, export_path)
                    self.stdout.write(
                        self.style.SUCCESS(f"Exported {len(generated_players)} newly created players to {filepath}"))
                else:
                    self.stdout.write(self.style.WARNING("No players were added to DB to export."))

        # 2. Generowanie tylko dla eksportu (bez dodawania do DB)
        elif num_players_to_generate > 0 and export_to_file:
            generated_players = self.generate_players(num_players_to_generate, clubs, categories)
            if generated_players:
                filepath = self.export_players_to_csv(generated_players, export_path)
                self.stdout.write(
                    self.style.SUCCESS(f"Generated and exported {len(generated_players)} players to {filepath}"))
            else:
                self.stdout.write(self.style.WARNING("No players were generated for export."))


        # 3. Eksport istniejących graczy (gdy --number=0 i --exporttofile)
        elif export_to_file and num_players_to_generate == 0 and not add_to_db:
            self.stdout.write("Exporting existing players from database...")
            # Użyj prefetch_related dla optymalizacji pobierania kategorii
            existing_players = list(Player.objects.prefetch_related('categories', 'club').all())
            if not existing_players:
                self.stdout.write(self.style.WARNING("No players found in database to export."))
            else:
                filepath = self.export_players_to_csv(existing_players, export_path)
                self.stdout.write(
                    self.style.SUCCESS(f"Exported {len(existing_players)} existing players to {filepath}"))

        # 4. Brak akcji
        elif not num_players_to_generate and not clear_players and not export_to_file:
            self.stdout.write(self.style.WARNING(
                "No action specified. Use --number with --addtodb or --exporttofile, or --clear, or just --exporttofile to export existing."
            ))

