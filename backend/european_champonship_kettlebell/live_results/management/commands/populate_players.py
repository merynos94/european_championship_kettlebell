import random
import csv
import os
from typing import List, Optional, Set

# Third-party imports
import factory
from factory.django import DjangoModelFactory
from faker import Faker

# Django imports
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from ...models.player import Player
from ...models.sport_club import SportClub
from ...models.category import Category
from ...models.constants import AVAILABLE_DISCIPLINES

# --- Faker Instance ---
fake = Faker('pl_PL')

# --- Constants ---
CATEGORY_NAMES = [
    "Amator Kobiet 65 kg / Woman Amateur 65 kg",
    "Amator Kobiet +65 kg / Woman Amateur +65 kg",
    "Amator Mężczyzn 85 kg / Man Amateur 85 kg",
    "Amator Mężczyzn +85 kg / Man Amateur +85 kg",
    "Pro Kobiet 65 kg / Woman Professional 65 kg",
    "Pro Kobiet +65 kg / Woman Professional +65 kg",
    "Pro Mężczyzn 85 kg / Man Professional 85 kg",
    "Pro Mężczyzn +85 kg / Man Professional +85 kg",
    "Junior 16 Dziewcząt / Girls Junior 16",
    "Junior 16 Chłopców / Boys Junior 16",
    "Masters +45 Kobiet / Woman Masters +45",
    "Masters +45 Mężczyzn / Man Masters +45",
    "Najlepsza Ząbkowiczanka / Woman Local",
    "Najlepszy Ząbkowiczanin / Man Local",
]

# --- Factory Definitions ---

class SportClubFactory(DjangoModelFactory):
    class Meta:
        model = SportClub
        django_get_or_create = ('name',)

    name = factory.Faker('company', locale='pl_PL')


class CategoryFactory(DjangoModelFactory):
    class Meta:
        model = Category
        django_get_or_create = ('name',)

    name = factory.Iterator(CATEGORY_NAMES) # Used implicitly by get_or_create if needed

    @factory.lazy_attribute
    def disciplines(self):
        all_discipline_codes = [code for code, name in AVAILABLE_DISCIPLINES]
        # Ensure disciplines list isn't empty if AVAILABLE_DISCIPLINES is empty
        if not all_discipline_codes:
            return []
        k = random.randint(1, min(4, len(all_discipline_codes)))
        return random.sample(all_discipline_codes, k=k)


class PlayerFactory(DjangoModelFactory):
    class Meta:
        model = Player

    name = factory.Faker('first_name', locale='pl_PL')
    surname = factory.Faker('last_name', locale='pl_PL')
    weight = 0.0
    club = factory.SubFactory(SportClubFactory)

class Command(BaseCommand):
    help = 'Populates the database with sample player data using Factory Boy and exports to CSV. By default, uses categories defined in CATEGORY_NAMES constant, ensuring they exist in DB. Use --use-categories to specify others from DB.'

    # --- Command Arguments ---
    def add_arguments(self, parser):
        # Arguments remain the same
        parser.add_argument('--number', type=int, default=0, help='Number of players to generate')
        parser.add_argument('--clubs', type=int, default=10, help='Target number of sport clubs to ensure exist')
        parser.add_argument('--clear', action='store_true', help='Clear existing Players (keeps Categories and SportClubs)')
        parser.add_argument('--exporttofile', action='store_true', help='Generate and export players to CSV file (default: fake_zawodnicy.csv)')
        parser.add_argument('--addtodb', action='store_true', help='Add generated players to the database (if --number > 0)')
        parser.add_argument('--export-path', type=str, default='.', help='Path where to save CSV file (default: current directory)')
        parser.add_argument(
            '--use-categories',
            type=str,
            default=None,
            help='Comma-separated list of specific category names to use (e.g., "Junior,Senior"). If provided, ignores CATEGORY_NAMES constant and uses only these (must exist in DB).'
        )

    # --- Helper Methods ---

    def _ensure_clubs(self, target_count: int) -> List[SportClub]:
        """Ensures at least target_count clubs exist, creating if necessary. Returns a list of clubs to use."""
        existing_clubs = SportClub.objects.all()
        current_count = existing_clubs.count()

        if current_count < target_count:
            num_to_create = target_count - current_count
            SportClubFactory.create_batch(num_to_create)
            self.stdout.write(f"Created {num_to_create} new Sport Clubs.")
            return list(SportClub.objects.all())
        elif current_count > target_count:
             self.stdout.write(f"Using first {target_count} of {current_count} existing Sport Clubs.")
             return list(existing_clubs[:target_count])
        else:
            self.stdout.write(f"Using {current_count} existing Sport Clubs.")
            return list(existing_clubs)

    # --- MODIFIED METHOD ---
    def _get_categories_to_use(self, target_names_str: Optional[str]) -> List[Category]:
        """
        Determines the list of Category DB objects to use for player assignment.
        If --use-categories is provided, fetches only those specific categories from DB.
        Otherwise, ensures categories listed in CATEGORY_NAMES constant exist in DB
        and returns only those DB objects.
        """
        if target_names_str:
            # --- Use categories specified by the user ---
            target_names: Set[str] = {name.strip() for name in target_names_str.split(',') if name.strip()}
            self.stdout.write(f"Using categories specified via --use-categories: {', '.join(sorted(target_names))}")

            # Fetch ONLY the specified categories from DB
            categories_to_use = list(Category.objects.filter(name__in=target_names))
            found_names: Set[str] = {cat.name for cat in categories_to_use}

            missing_names: Set[str] = target_names - found_names
            if missing_names:
                raise CommandError(f"Specified categories not found in DB: {', '.join(sorted(missing_names))}. Please ensure they exist.")

            if not categories_to_use:
                 raise CommandError(f"None of the specified categories ({target_names_str}) were found in the DB.")

            self.stdout.write(f"Found {len(categories_to_use)} specified categories in DB.")
            return categories_to_use
        else:
            # --- Default: Use categories from CATEGORY_NAMES constant ---
            self.stdout.write("Using categories defined in the CATEGORY_NAMES constant.")

            if not CATEGORY_NAMES:
                self.stderr.write(self.style.WARNING("CATEGORY_NAMES constant is empty. No categories available for default assignment."))
                return []

            categories_from_constant = []
            created_count = 0
            retrieved_count = 0

            # Ensure each category from the constant exists in the DB
            for name in CATEGORY_NAMES:
                try:
                    # get_or_create returns (object, created_boolean)
                    # Use defaults from CategoryFactory if creating
                    category_obj, created = Category.objects.get_or_create(
                        name=name,
                        # Optionally provide defaults if CategoryFactory doesn't handle them
                        # defaults={'disciplines': CategoryFactory.disciplines.function()}
                    )
                    categories_from_constant.append(category_obj)
                    if created:
                        created_count += 1
                        # Assign disciplines if newly created and factory didn't (e.g., if defaults not used)
                        if not category_obj.disciplines:
                             all_discipline_codes = [code for code, name_ in AVAILABLE_DISCIPLINES]
                             if all_discipline_codes:
                                 k = random.randint(1, min(4, len(all_discipline_codes)))
                                 category_obj.disciplines = random.sample(all_discipline_codes, k=k)
                                 category_obj.save()

                    else:
                        retrieved_count += 1
                except Exception as e:
                    # Catch potential errors during get_or_create (e.g., DB issues, validation)
                    self.stderr.write(self.style.ERROR(f"Error getting or creating category '{name}': {e}"))
                    # Decide if you want to stop or continue; continuing here
                    continue

            if created_count > 0:
                self.stdout.write(f"Created {created_count} missing categories from CATEGORY_NAMES in the database.")
            if retrieved_count > 0:
                 self.stdout.write(f"Retrieved {retrieved_count} existing categories corresponding to CATEGORY_NAMES from the database.")

            if not categories_from_constant:
                 self.stderr.write(self.style.WARNING("Could not retrieve or create any categories based on CATEGORY_NAMES."))

            return categories_from_constant

    def _assign_random_categories(self, player: Player, available_categories: List[Category]):
        """Assigns 1 to 3 random categories from the available list to a player."""
        # This method remains the same - it works with a list of Category objects
        if not available_categories:
            return

        max_cats_to_assign = min(3, len(available_categories))
        if max_cats_to_assign < 1:
            return
        num_cats_to_assign = random.randint(1, max_cats_to_assign)
        assigned_categories = random.sample(available_categories, num_cats_to_assign)

        if hasattr(player, 'pk') and player.pk:
            player.categories.set(assigned_categories)
            player._assigned_categories_cache = assigned_categories
        else:
            player._categories = assigned_categories

    def generate_players_in_memory(self, num_players: int, clubs: List[SportClub], categories_to_use: List[Category]) -> List[Player]:
        """Generates player objects in memory (not saved to DB)."""
        # This method remains the same
        self.stdout.write(f"Generating {num_players} players in memory...")
        players = []
        if not clubs:
            self.stderr.write(self.style.ERROR("No clubs available to assign."))
            return []
        if not categories_to_use:
            self.stderr.write(self.style.WARNING("No categories available to assign during in-memory generation. Players will have no categories."))

        for i in range(num_players):
            club = random.choice(clubs)
            player = PlayerFactory.build(club=club)
            self._assign_random_categories(player, categories_to_use)
            players.append(player)

        self.stdout.write(f"Generated {len(players)} players in memory.")
        return players

    def export_players_to_csv(self, players: List[Player], export_path: str) -> str:
        """Exports a list of player objects (DB or memory) to a CSV file."""
        # This method remains the same
        filepath = os.path.join(export_path, 'fake_zawodnicy.csv')
        os.makedirs(export_path, exist_ok=True)
        self.stdout.write(f"Exporting {len(players)} players to {filepath}...")

        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['id', 'name', 'surname', 'club', 'categories']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for player in players:
                player_id = getattr(player, 'pk', '')
                club_name = getattr(getattr(player, 'club', None), 'name', '')

                player_categories = []
                if hasattr(player, '_assigned_categories_cache'):
                    player_categories = player._assigned_categories_cache
                elif hasattr(player, '_categories'):
                    player_categories = player._categories
                elif player_id:
                    try:
                        player_categories = list(player.categories.all())
                    except Exception as e:
                        self.stderr.write(self.style.ERROR(f"Error getting categories for player ID {player_id}: {e}"))

                categories_str = ','.join(sorted([cat.name for cat in player_categories]))

                writer.writerow({
                    'id': player_id,
                    'name': getattr(player, 'name', ''),
                    'surname': getattr(player, 'surname', ''),
                    'club': club_name,
                    'categories': categories_str
                })

        self.stdout.write(self.style.SUCCESS(f"Successfully exported data to {filepath}"))
        return filepath

    # --- Main Command Logic ---
    @transaction.atomic
    def handle(self, *args, **options):
        # This method remains largely the same, relying on the modified _get_categories_to_use
        num_players_to_generate: int = options['number']
        num_clubs_target: int = options['clubs']
        clear_players: bool = options['clear']
        export_to_file: bool = options['exporttofile']
        add_to_db: bool = options['addtodb']
        export_path: str = options['export_path']
        target_category_names_str: Optional[str] = options['use_categories']

        # 1. Clear existing players if requested
        if clear_players:
            self.stdout.write(self.style.WARNING('Clearing existing Player data...'))
            count, _ = Player.objects.all().delete()
            self.stdout.write(self.style.SUCCESS(f'Player data cleared ({count} deleted).'))

        # 2. Ensure required clubs and determine categories to use
        try:
            clubs_to_use = self._ensure_clubs(num_clubs_target)
            if not clubs_to_use and num_players_to_generate > 0:
                 raise CommandError("No Sport Clubs available or could be created. Cannot generate players.")

            # Get categories based on the new logic (flag or CATEGORY_NAMES constant)
            categories_to_use = self._get_categories_to_use(target_category_names_str)

            if not categories_to_use and num_players_to_generate > 0:
                 self.stderr.write(self.style.WARNING("No categories selected or available to assign. Players will be generated without categories."))
                 # If categories MUST exist, raise CommandError here:
                 # raise CommandError("Cannot generate players: No categories available or specified.")

        except CommandError as e:
            raise e # Propagate CommandErrors to stop execution

        # 3. Perform requested actions
        generated_players_this_run: List[Player] = []

        # Action: Generate and add to Database
        if num_players_to_generate > 0 and add_to_db:
            self.stdout.write(f"Creating {num_players_to_generate} players and adding to database using selected categories...")
            for _ in range(num_players_to_generate):
                club = random.choice(clubs_to_use)
                player = PlayerFactory(club=club)
                self._assign_random_categories(player, categories_to_use)
                generated_players_this_run.append(player)

            self.stdout.write(self.style.SUCCESS(f"Successfully created and saved {len(generated_players_this_run)} players to database."))

            if export_to_file:
                self.export_players_to_csv(generated_players_this_run, export_path)

        # Action: Generate for export only (not adding to DB)
        elif num_players_to_generate > 0 and export_to_file:
            players_for_export = self.generate_players_in_memory(num_players_to_generate, clubs_to_use, categories_to_use)
            if players_for_export:
                self.export_players_to_csv(players_for_export, export_path)
            else:
                self.stdout.write(self.style.WARNING("No players were generated for export (possibly due to lack of clubs)."))

        # Action: Export existing players from DB only
        elif export_to_file and num_players_to_generate == 0 and not add_to_db:
            self.stdout.write("Exporting existing players from database...")
            existing_players = list(Player.objects.prefetch_related('categories', 'club').all())
            if not existing_players:
                self.stdout.write(self.style.WARNING("No players found in database to export."))
            else:
                self.export_players_to_csv(existing_players, export_path)

        # No action specified
        elif not any([clear_players, export_to_file, add_to_db and num_players_to_generate > 0]):
             self.stdout.write(self.style.WARNING(
                "No action performed. Use --number with --addtodb or --exporttofile, or --clear, or just --exporttofile to export existing."
            ))