from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()

router.register(r'categories', views.CategoryViewSet, basename='category')


router.register(r'sportclubs', views.SportClubViewSet, basename='sportclub')
urlpatterns = [
    path('', include(router.urls)),
    path('lista-startowa/', views.generate_start_list, name='generate_start_list'),

]
