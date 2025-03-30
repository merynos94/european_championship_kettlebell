"""European Kettlebell Championships Admin panel"""

from decimal import Decimal

from django.contrib import admin

from .models import Athlete, AthleteCategory, Category, Club, Exercise, ExerciseType


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    """Admin panel configuration for Club model."""

    list_display = ("name", "count_athletes")
    search_fields = ("name",)
    list_filter = ("name",)

    def count_athletes(self, obj):
        """Display the number of athletes in this club."""
        return obj.athletes.count()

    count_athletes.short_description = "Liczba zawodników"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin panel configuration for Category model."""

    list_display = ("name", "count_athletes")
    search_fields = ("name",)

    def count_athletes(self, obj):
        """Display the number of athletes in this category."""
        return obj.athletes.count()

    count_athletes.short_description = "Liczba zawodników"


@admin.register(ExerciseType)
class ExerciseTypeAdmin(admin.ModelAdmin):
    """Admin panel configuration for ExerciseType model."""

    list_display = ("name", "calculation_method", "attempts_count", "is_active", "display_categories")
    list_filter = ("calculation_method", "is_active", "categories")
    search_fields = ("name", "description")
    filter_horizontal = ("categories",)

    def display_categories(self, obj):
        """Display all categories this exercise is used in."""
        return ", ".join([c.name for c in obj.categories.all()])

    display_categories.short_description = "Kategorie"


class AthleteCategoryInline(admin.TabularInline):
    """Inline form for AthleteCategory within Athlete admin."""

    model = AthleteCategory
    extra = 1
    autocomplete_fields = ["category"]


class ExerciseInline(admin.TabularInline):
    """Inline form for Exercise results within Athlete admin."""

    model = Exercise
    extra = 0
    fields = (
        "exercise_type",
        "category",
        "kettlebell_weight",
        "repetitions",
        "attempt1_weight",
        "attempt2_weight",
        "attempt3_weight",
        "display_score",
    )
    readonly_fields = ("display_score",)
    autocomplete_fields = ["exercise_type", "category"]

    def display_score(self, obj):
        """Display calculated score for this exercise."""
        if obj.id:  # Only calculate if object exists in database
            return f"{obj.calculate_score():.2f}"
        return "-"

    display_score.short_description = "Wynik"


@admin.register(Athlete)
class AthleteAdmin(admin.ModelAdmin):
    """Admin panel configuration for Athlete model."""

    list_display = ("last_name", "first_name", "club", "body_weight", "display_categories")
    list_filter = ("club", "categories")
    search_fields = ("first_name", "last_name", "club__name")
    fieldsets = (("Dane podstawowe", {"fields": ("first_name", "last_name", "body_weight", "club", "notes")}),)
    inlines = [AthleteCategoryInline, ExerciseInline]
    autocomplete_fields = ["club"]

    def display_categories(self, obj):
        """Display all categories this athlete participates in."""
        return ", ".join([c.name for c in obj.categories.all()])

    display_categories.short_description = "Kategorie"

    def get_queryset(self, request):
        """Optimize queries by prefetching related objects."""
        return super().get_queryset(request).prefetch_related("categories", "club")


@admin.register(AthleteCategory)
class AthleteCategoryAdmin(admin.ModelAdmin):
    """Admin panel configuration for AthleteCategory model."""

    list_display = ("athlete", "category", "place", "points", "tiebreaker", "display_total_points")
    list_filter = ("category", "tiebreaker")
    search_fields = ("athlete__first_name", "athlete__last_name", "category__name")
    autocomplete_fields = ["athlete", "category"]
    list_editable = ("place", "tiebreaker")

    actions = ["calculate_points_from_place", "calculate_places_from_scores"]

    def display_total_points(self, obj):
        """Display total points including tiebreaker."""
        total = obj.points
        if obj.tiebreaker:
            total -= Decimal("0.5")
        return total

    display_total_points.short_description = "Suma punktów"

    @admin.action(description="Oblicz punkty na podstawie miejsca")
    def calculate_points_from_place(self, request, queryset):
        """Calculate points based on place (1st place = 1 point, etc.)."""
        updated = 0
        for obj in queryset:
            if obj.place is not None and obj.place > 0:
                obj.points = obj.place
                obj.save()
                updated += 1

        self.message_user(request, f"Zaktualizowano punkty dla {updated} zawodników.")

    @admin.action(description="Oblicz miejsca na podstawie wyników")
    def calculate_places_from_scores(self, request, queryset):
        """Calculate places based on exercise scores within each category."""
        # Group by category
        categories = set(queryset.values_list("category", flat=True))
        updated = 0

        for category_id in categories:
            # Get all athletes in this category
            athletes_in_category = queryset.filter(category_id=category_id)

            # Calculate total scores for each athlete in this category
            athlete_scores = []
            for enrollment in athletes_in_category:
                total_score = 0
                for exercise in Exercise.objects.filter(athlete=enrollment.athlete, category_id=category_id):
                    total_score += exercise.calculate_score()

                athlete_scores.append((enrollment, total_score))

            # Sort by score (higher is better)
            athlete_scores.sort(key=lambda x: x[1], reverse=True)

            # Assign places
            for place, (enrollment, _) in enumerate(athlete_scores, 1):
                enrollment.place = place
                enrollment.points = place  # Set points equal to place
                enrollment.save()
                updated += 1

        self.message_user(request, f"Obliczono miejsca i punkty dla {updated} zawodników na podstawie wyników.")


class AthleteFilter(admin.SimpleListFilter):
    """Custom filter for Exercise admin to filter by athlete."""

    title = "Zawodnik"
    parameter_name = "athlete"

    def lookups(self, request, model_admin):
        """Return all athletes as filter options."""
        athletes = Athlete.objects.all().order_by("last_name", "first_name")
        return [(a.id, f"{a.last_name} {a.first_name}") for a in athletes]

    def queryset(self, request, queryset):
        """Filter queryset by selected athlete."""
        if self.value():
            return queryset.filter(athlete_id=self.value())
        return queryset


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    """Admin panel configuration for Exercise model."""

    list_display = ("athlete", "exercise_type", "category", "display_score", "display_details")
    list_filter = ("exercise_type", "category", AthleteFilter)
    search_fields = ("athlete__first_name", "athlete__last_name", "exercise_type__name")
    autocomplete_fields = ["athlete", "exercise_type", "category"]

    fieldsets = (
        ("Podstawowe informacje", {"fields": ("athlete", "exercise_type", "category")}),
        (
            "Wyniki Snatch",
            {
                "fields": ("kettlebell_weight", "repetitions"),
                "classes": ("collapse",),
                "description": "Pola używane dla ćwiczenia typu Snatch (waga × powtórzenia).",
            },
        ),
        (
            "Wyniki prób (TGU, Press, Squat)",
            {
                "fields": ("attempt1_weight", "attempt2_weight", "attempt3_weight"),
                "classes": ("collapse",),
                "description": "Pola używane dla ćwiczeń z wieloma próbami.",
            },
        ),
    )

    def display_score(self, obj):
        """Display calculated score for this exercise."""
        score = obj.calculate_score()
        return f"{score:.2f}"

    display_score.short_description = "Wynik"

    def display_details(self, obj):
        """Display exercise details based on type."""
        if obj.exercise_type.calculation_method == "weight_x_reps":
            return f"{obj.kettlebell_weight}kg × {obj.repetitions}"
        else:
            attempts = [f"{obj.attempt1_weight}kg", f"{obj.attempt2_weight}kg", f"{obj.attempt3_weight}kg"]
            return " / ".join(attempts)

    display_details.short_description = "Szczegóły"

    def get_queryset(self, request):
        """Optimize queries by prefetching related objects."""
        return super().get_queryset(request).select_related("athlete", "exercise_type", "category")
