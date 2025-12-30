import requests
from django.shortcuts import render
import re

def home(request):
    context = {} 
    
    return render(request, 'home.html', context)


def pokedex(request):
    try:
        # O limite 1025 garante que pegar até o fim da 9ª geração (Pecharunt)
        response = requests.get('https://pokeapi.co/api/v2/pokemon-species?limit=1025')
        data = response.json()
        
        pokemons = []
        for pokemon in data['results']:
            # Extraímos a entrada da pokedex da URL, criando um int.
            pokemon_id = int(pokemon['url'].split('/')[-2]) # A cada / o texto é separado e no final ele pega a posição -2 da lista criada e transforma em INT
            
            # Limpa o nome tirando os "-"
            display_name = pokemon['name'].replace('-', ' ').title()
            
            # Apenas deixa os nomes com hifén (casos especiais)
            if display_name == "Ho Oh": display_name = "Ho-Oh"
            if display_name == "Porygon Z": display_name = "Porygon-Z"

            pokemons.append({
                'id': pokemon_id, # Número da pokedex
                'name': display_name, # Nome fora do formato slug
                'url_name': pokemon['name'] # Tratamento de url para futura pagina de detalhes 
            })
        
        # Ordena por entrada da pokedex
        pokemons.sort(key=lambda x: x['id']) # Lambda para otimizar o codigo sem criar uma função extra para ordenar (Os "x": 1°- Pokémon(parametro), 2°-ID(return da func))
        
        context = {
            'pokemons': pokemons,
            'total': len(pokemons)
        }
        return render(request, 'pokedex.html', context)
        
    except Exception as e: # Só para erros
        return render(request, 'pokedex.html', {'pokemons': [], 'error': str(e)})

def detalhe_pokemon(request, pokemon_id):
    # Passamos apenas o ID, o resto o JS busca
    return render(request, 'detalhe_pokemon.html', {'pokemon_id': pokemon_id})