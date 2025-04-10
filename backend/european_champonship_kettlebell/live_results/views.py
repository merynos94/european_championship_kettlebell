from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Prefetch

# Import your models
from .models import Category, OverallResult, Player, SportClub # Import necessary models
# Import your serializers
from .serializers import (
    CategorySerializer,
    CategoryResultsSerializer,
    SportClubSerializer, # Add if you want an endpoint for clubs
    PlayerBasicInfoSerializer, # May be needed for other endpoints
    # ... import other serializers if creating separate endpoints for them ...
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

    # Custom 'results' action available for a specific category instance
    # Will be available at URL like /api/categories/{pk}/results/
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
            Prefetch('player__see_saw_press_result'),
            Prefetch('player__kb_squat_result'),
            Prefetch('player__pistol_squat_result'),
            Prefetch('player__one_kettlebell_press_result'),
            Prefetch('player__two_kettlebell_press_result'),
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

# --- Optional: ViewSet for Players ---
# You might want a general endpoint for searching/listing players,
# independent of category, e.g., for autocompletion.
# Use PlayerBasicInfoSerializer or a full PlayerSerializer as needed.
# class PlayerViewSet(viewsets.ReadOnlyModelViewSet):
#     """ViewSet for listing/searching players."""
#     queryset = Player.objects.select_related('club').prefetch_related('categories').order_by('surname', 'name')
#     serializer_class = PlayerSerializer # Or PlayerBasicInfoSerializer
#     permission_classes = [permissions.AllowAny] # Or others
#     # Filtering could be added, e.g., by surname:
#     # filter_backends = [filters.SearchFilter]
#     # search_fields = ['name', 'surname', 'club__name']