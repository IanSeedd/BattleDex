import requests
from django.shortcuts import render
import re

def pokedex(request):
    try:
        # Busca TODOS os pokémons de uma vez
        response = requests.get('https://pokeapi.co/api/v2/pokemon?limit=1300')
        data = response.json()
        
        pokemons = []
        
        # Lista de nomes base que já processamos
        processed_bases = set()
        
        for pokemon in data['results']:
            pokemon_id = pokemon['url'].split('/')[-2]
            pokemon_name = pokemon['name']
            
            # Extrai nome base (primeira parte antes do hífen)
            base_name = pokemon_name.split('-')[0]
            
            # Se for um número, é provavelmente uma forma especial
            if re.search(r'-\d+$', pokemon_name):
                continue
            
            # Lista de formas que devem ser ignoradas
            ignore_patterns = [
                '-mega', '-gmax', '-totem', '-eternamax', '-primal',
                '-alola', '-galar', '-hisui', '-paldea',
                '-segment', '-hero', '-disguised', '-busted',
                '-amped', '-low-key', '-midday', '-midnight', '-dusk', '-dawn',
                '-ash', '-partner', '-cap', '-origin', '-school',
                '-therian', '-blade', '-complete',
                '-sunny', '-rainy', '-snowy',
                '-attack', '-defense', '-speed',
                '-red', '-blue', '-green', '-yellow', '-orange', '-indigo', '-violet',
                '-meteor', '-pau', '-pom-pom', '-baile', '-sensu',
                '-ice', '-frost', '-heat', '-wash', '-fan', '-mow', '-trash', '-sky',
                '-land', '-incarnate', '-male', '-female',
                '-average', '-small', '-large', '-super',
                '-10', '-50', '-100', '-west', '-east'
            ]
            
            # Verifica se é uma forma que deve ser ignorada
            should_ignore = False
            for pattern in ignore_patterns:
                if pattern in pokemon_name:
                    should_ignore = True
                    break
            
            if should_ignore:
                continue
            
            # Se o nome base já foi processado e este tem hífen, pula
            # (exceto para pokémons que naturalmente têm hífen no nome)
            exceptions_with_hyphen = [
                'ho-oh', 'porygon-z', 'jangmo-o', 'hakamo-o', 'kommo-o',
                'type-null', 'tapu-koko', 'tapu-lele', 'tapu-bulu', 'tapu-fini',
                'mr-mime', 'mr-rime', 'mime-jr', 'wo-chien', 'chien-pao',
                'ting-lu', 'chi-yu', 'great-tusk', 'scream-tail', 'brute-bonnet',
                'flutter-mane', 'slither-wing', 'sandy-shocks', 'iron-treads',
                'iron-bundle', 'iron-hands', 'iron-jugulis', 'iron-moth',
                'iron-thorns', 'roaring-moon', 'iron-valiant', 'walking-wake',
                'iron-leaves'
            ]
            
            if base_name in processed_bases and '-' in pokemon_name and pokemon_name not in exceptions_with_hyphen:
                continue
            
            # Formata o nome para exibição
            display_name = pokemon_name
            if '-' in pokemon_name and pokemon_name not in exceptions_with_hyphen:
                # Para nomes com hífen, pega apenas a primeira parte
                display_name = base_name
            
            display_name = display_name.replace('-', ' ').title()
            
            pokemons.append({
                'id': int(pokemon_id),
                'name': display_name,
                'original_name': pokemon_name
            })
            
            processed_bases.add(base_name)
        
        # Remove duplicatas por nome de exibição
        unique_pokemons = []
        seen_names = set()
        
        for pokemon in pokemons:
            if pokemon['name'] not in seen_names:
                unique_pokemons.append(pokemon)
                seen_names.add(pokemon['name'])
        
        # Ordena por ID
        unique_pokemons.sort(key=lambda x: x['id'])
        
        print(f"Total de Pokémon únicos: {len(unique_pokemons)}")
        
        # Log dos primeiros 10 para debug
        for i, p in enumerate(unique_pokemons[:10]):
            print(f"{i+1}. #{p['id']:04d} - {p['name']} ({p['original_name']})")
        
        context = {
            'pokemons': unique_pokemons,
            'total': len(unique_pokemons)
        }
        return render(request, 'pokedex.html', context)
        
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()
        return render(request, 'pokedex.html', {'pokemons': [], 'error': str(e)})