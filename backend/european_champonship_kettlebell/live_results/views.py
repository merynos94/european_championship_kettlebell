from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Prefetch

from django.shortcuts import render
from django.db.models import Q
from .forms import StationForm
from .models import Category, OverallResult, Player, SportClub # Import necessary models
from .serializers import (
    CategorySerializer,
    CategoryResultsSerializer,
    SportClubSerializer, # Add if you want an endpoint for clubs
    PlayerBasicInfoSerializer, 
)

# --- ViewSet for Categories and their Results ---
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet providing a list of categories and (via a custom action)
    detailed results for a selected category.
    """
    queryset = Category.objects.order_by('name') # Get all categories, sorted by name
    serializer_class = CategorySerializer       # Use the simple serializer for category list/detail
    permission_classes = [permissions.AllowAny] # Allow anyone to read categories (can change to IsAuthenticatedOrReadOnly)

    @action(detail=True, methods=['get'], url_path='results', serializer_class=CategoryResultsSerializer)
    def results(self, request, pk=None):
        """
        Returns a sorted list of overall results (OverallResult)
        for players belonging to the given category (specified by pk).
        Includes nested player data and their results in disciplines.
        """
        # self.get_object() retrieves the Category instance based on 'pk' from the URL
        # and automatically handles 404 errors if the category doesn't exist.
        category = self.get_object()

        # Build the queryset for OverallResult, filtering by player's category
        queryset = OverallResult.objects.filter(
            player__categories=category
        ).select_related(
            # Optimization: Fetch related objects with a single SQL query
            'player',         # Fetch the Player object
            'player__club'    # Also fetch the Club object related to the Player
        ).prefetch_related(
            # Optimization: Fetch all related discipline results with one query per result type for all players
            # Use the correct 'related_name' defined in OneToOneField relations in result models
            Prefetch('player__snatch_result'), # Using Prefetch is more explicit
            Prefetch('player__tgu_result'),
            Prefetch('player__kb_squat_one_result'),
            Prefetch('player__one_kettlebell_press_result'),
            Prefetch('player__two_kettlebell_press_one_result'),
            # Prefetch('player__categories'), # Rarely needed here unless displaying player's categories in PlayerBasicInfoSerializer
        ).order_by(
            'final_position', # Sort by final position within the category
            'player__surname', # Secondary sort for ties by surname
            'player__name'     # Further sort for ties by name
        )

        # Paginate results (good practice for lists)
        # Pagination needs to be configured globally in base.py
        # or a pagination class defined for this ViewSet for this to work effectively.
        page = self.paginate_queryset(queryset)
        if page is not None:
            # Use the serializer_class defined in the @action decorator here
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # Return data if pagination is not active/configured
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

# --- Optional: ViewSet for Sport Clubs ---
class SportClubViewSet(viewsets.ReadOnlyModelViewSet):
    """Simple ViewSet for listing sport clubs."""
    queryset = SportClub.objects.order_by('name')
    serializer_class = SportClubSerializer
    permission_classes = [permissions.AllowAny] # Or others
    


def generate_start_list(request):
    if request.method == "POST":
        form = StationForm(request.POST)
        if form.is_valid():
            category_names = form.cleaned_data["categories"]
            stations_count = form.cleaned_data["stations"]
            distribute_evenly = form.cleaned_data["distribute_evenly"]

            # Sprawdzenie poprawności danych
            if stations_count <= 0:
                form.add_error("stations", "Liczba stanowisk musi być większa od 0.")
                return render(request, "station_form.html", {"form": form})
            
            if not category_names:
                form.add_error("categories", "Wybierz co najmniej jedną kategorię.")
                return render(request, "station_form.html", {"form": form})

            # Wyszukanie zawodników ze wszystkich wybranych kategorii
            query = Q()
            for category_name in category_names:
                query |= Q(categories__name=category_name)
            
            players = Player.objects.filter(query).distinct().order_by("surname", "name")
            player_count = players.count()

            # Sprawdzenie czy są zawodnicy
            if player_count == 0:
                categories_display = ", ".join(category_names)
                return render(
                    request,
                    "start_list.html",
                    {
                        "message": f"Brak zawodników w wybranych kategoriach: {categories_display}.",
                        "categories": categories_display,
                        "stations": stations_count,
                    },
                )

            # Rozdzielenie zawodników na stanowiska
            if distribute_evenly:
                # Równomierne rozdzielenie
                players_per_station = (player_count + stations_count - 1) // stations_count
                stations_list = []
                
                for i in range(stations_count):
                    start_idx = i * players_per_station
                    end_idx = min((i + 1) * players_per_station, player_count)
                    
                    if start_idx >= player_count:
                        # Puste stanowisko, gdy zabraknie zawodników
                        stations_list.append({
                            "station_number": i + 1,
                            "players": [],
                        })
                    else:
                        stations_list.append({
                            "station_number": i + 1,
                            "players": players[start_idx:end_idx],
                        })
            else:
                # Rozdzielenie po kolei (1 zawodnik na stanowisko, potem kolejny cykl)
                stations_list = [{"station_number": i + 1, "players": []} for i in range(stations_count)]
                
                for idx, player in enumerate(players):
                    station_idx = idx % stations_count
                    stations_list[station_idx]["players"].append(player)

            # Przygotowanie nazwy kategorii do wyświetlenia
            categories_display = ", ".join([name.replace("_", " ") for name in category_names])
            
            return render(
                request,
                "start_list.html",
                {
                    "stations_list": stations_list,
                    "stations": stations_count,
                    "categories": categories_display,
                    "player_count": player_count,
                    "distribute_type": "równomiernie" if distribute_evenly else "cyklicznie",
                },
            )
    else:
        form = StationForm()

    return render(request, "station_form.html", {"form": form})
