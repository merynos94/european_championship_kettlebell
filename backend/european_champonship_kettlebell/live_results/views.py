# Plik: views.py

from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Prefetch, Q # Q jest potrzebne dla generate_start_list
from django.shortcuts import render, get_object_or_404 # Dodano get_object_or_404

from .forms import StationForm # Upewnij się, że ścieżka jest poprawna
# Importuj NOWY model CategoryOverallResult i inne potrzebne
from .models import Category, CategoryOverallResult, Player, SportClub
from .serializers import (
    CategorySerializer,
    CategoryResultsSerializer, # Ten serializer też został zmodyfikowany
    SportClubSerializer,
    # PlayerBasicInfoSerializer, # Już niepotrzebny bezpośrednio tutaj? Jest używany w CategoryResultsSerializer
    CategoryResultsSerializer,
    SportClubSerializer, # Add if you want an endpoint for clubs
    PlayerBasicInfoSerializer,
)

# Plik: views.py (fragment - CategoryResultsView)

from rest_framework import generics, permissions
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch # Potrzebne do prefetch

# Importuj NOWY model i serializer, oraz Category, Player (Player może nie być potrzebny bezpośrednio)
from .models.results.overall import CategoryOverallResult # Poprawna ścieżka?
from .serializers import CategoryResultsSerializer
from .models import Category # Potrzebne do get_object_or_404

class CategoryResultsView(generics.ListAPIView):
    serializer_class = CategoryResultsSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        category_id = self.kwargs.get('category_id')
        category = get_object_or_404(Category, pk=category_id) # Pobierz kategorię

        queryset = CategoryOverallResult.objects.filter(
            category=category # Filtruj po kategorii
        ).select_related(
            'player',
            'player__club'
        ).prefetch_related(
            # Użyj poprawnych related_name z modelu Player!
            Prefetch('player__snatch_result'),
            Prefetch('player__tgu_result'),
            Prefetch('player__kb_squat_one_result'),
            Prefetch('player__one_kettlebell_press_result'),
            Prefetch('player__two_kettlebell_press_one_result'),
        ).order_by(
            'final_position', 'total_points', 'player__surname', 'player__name'
        )
        return queryset
# --- ViewSet for Categories and their Results ---
class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet dostarczający listę kategorii oraz (przez akcję)
    szczegółowe wyniki dla wybranej kategorii.
    """
    queryset = Category.objects.order_by('name')
    serializer_class = CategorySerializer # Główny endpoint listy kategorii używa tego
    permission_classes = [permissions.AllowAny]

    # ZMIANA: serializer_class wskazuje na zmodyfikowany serializer
    @action(detail=True, methods=['get'], url_path='results', serializer_class=CategoryResultsSerializer)
    def results(self, request, pk=None):
        """
        Zwraca posortowaną listę wyników ogólnych (CategoryOverallResult)
        dla graczy w danej kategorii (pk).
        Zawiera zagnieżdżone dane gracza i wyniki w dyscyplinach.
        """
        # Pobierz obiekt kategorii lub zwróć 404
        category = get_object_or_404(Category, pk=pk)

        # --- ZMIANA GŁÓWNA: Zapytanie do nowego modelu ---
        # Budujemy queryset dla NOWEGO modelu CategoryOverallResult
        queryset = CategoryOverallResult.objects.filter(
            category=category # Filtrujemy bezpośrednio po kategorii
        ).select_related(
            # Optymalizacja: Pobierz powiązane obiekty jednym zapytaniem
            'player',         # Pobierz obiekt Player powiązany z CategoryOverallResult
            'player__club'    # Pobierz klub gracza przez relację z Player
        ).prefetch_related(
            # Optymalizacja: Pobierz wyniki dyscyplin dla graczy jednym zapytaniem per typ wyniku
            # Użyj poprawnych related_name z modelu Player!
            Prefetch('player__snatch_result'),
            Prefetch('player__tgu_result'),
            Prefetch('player__kb_squat_one_result'), # Sprawdź related_name!
            Prefetch('player__one_kettlebell_press_result'),
            Prefetch('player__two_kettlebell_press_one_result'), # Sprawdź related_name!
        ).order_by(
            # Sortuj wg miejsca końcowego w TEJ kategorii, potem punktów, potem nazwiska
            'final_position',
            'total_points',
            'player__surname',
            'player__name'
        )
        # --- KONIEC ZMIANY GŁÓWNEJ ---

        # Paginacja (bez zmian, ale upewnij się, że jest skonfigurowana)
        page = self.paginate_queryset(queryset)
        if page is not None:
            # Użyj serializera zdefiniowanego w @action
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # Zwróć dane bez paginacji
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

# --- Optional: ViewSet for Sport Clubs (bez zmian) ---
class SportClubViewSet(viewsets.ReadOnlyModelViewSet):
    """Prosty ViewSet do listowania klubów."""
    queryset = SportClub.objects.order_by('name')
    serializer_class = SportClubSerializer
    permission_classes = [permissions.AllowAny]

# --- Funkcja generate_start_list (bez zmian) ---
# Ta funkcja wydaje się niezwiązana z wyświetlaniem wyników i może pozostać bez zmian,
# o ile modele Player i Category nie zmieniły się w sposób wpływający na nią.
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

            # Wyszukanie zawodników (bez zmian)
            query = Q()
            for category_name in category_names:
                query |= Q(categories__name=category_name)
            players = Player.objects.filter(query).distinct().order_by("surname", "name")
            player_count = players.count()

            # Sprawdzenie czy są zawodnicy (bez zmian)
            if player_count == 0:
                categories_display = ", ".join(category_names)
                return render( request, "start_list.html", { "message": f"Brak zawodników w wybranych kategoriach: {categories_display}.", "categories": categories_display, "stations": stations_count, }, )

            # Rozdzielenie zawodników na stanowiska (bez zmian)
            if distribute_evenly:
                players_per_station = (player_count + stations_count - 1) // stations_count
                stations_list = []
                for i in range(stations_count):
                    start_idx = i * players_per_station
                    end_idx = min((i + 1) * players_per_station, player_count)
                    if start_idx >= player_count:
                        stations_list.append({"station_number": i + 1, "players": []})
                    else:
                        stations_list.append({"station_number": i + 1, "players": players[start_idx:end_idx]})
            else:
                stations_list = [{"station_number": i + 1, "players": []} for i in range(stations_count)]
                for idx, player in enumerate(players):
                    station_idx = idx % stations_count
                    stations_list[station_idx]["players"].append(player)

            # Renderowanie (bez zmian)
            categories_display = ", ".join([name.replace("_", " ") for name in category_names])
            return render( request, "start_list.html", { "stations_list": stations_list, "stations": stations_count, "categories": categories_display, "player_count": player_count, "distribute_type": "równomiernie" if distribute_evenly else "cyklicznie", }, )
    else:
        form = StationForm()

    return render(request, "station_form.html", {"form": form})