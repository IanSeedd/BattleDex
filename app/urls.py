from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('pokedex/', views.pokedex, name='pokedex'),
    path('pokedex/<int:pokemon_id>/', views.detalhe_pokemon, name='detalhe_pokemon'),
    path('box/', views.box_view, name='box'),   
    path('api/update_team/', views.update_team_slot, name='update_team'),   
    path('criar/', views.criar_pokemon_view, name='criar_pokemon'),
]