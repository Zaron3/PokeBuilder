"""
Script per marcar Pokémon com a prohibits en competitivo.
Pots modificar la llista de pokemon_ids_prohibits segons les regles del format que utilitzis.
"""
import requests
import json
import time

ELASTIC_URL = "http://localhost:9200"
INDEX_NAME = "pokemon"

# Llista d'IDs de Pokémon prohibits en competitivo
# Aquests són exemples - ajusta segons el format (VGC, Smogon, etc.)
# Exemples comuns: Mewtwo (150), Mew (151), Lugia (249), Ho-Oh (250), etc.
pokemon_ids_prohibits = [
    # Llegendaris Míticos (exemples)
    150,  # Mewtwo
    151,  # Mew
    249,  # Lugia
    250,  # Ho-Oh
    251,  # Celebi
    382,  # Kyogre
    383,  # Groudon
    384,  # Rayquaza
    385,  # Jirachi
    386,  # Deoxys
    483,  # Dialga
    484,  # Palkia
    487,  # Giratina
    489,  # Phione
    490,  # Manaphy
    491,  # Darkrai
    492,  # Shaymin
    493,  # Arceus
    494,  # Victini
    638,  # Cobalion
    639,  # Terrakion
    640,  # Virizion
    641,  # Tornadus
    642,  # Thundurus
    643,  # Reshiram
    644,  # Zekrom
    645,  # Landorus
    646,  # Kyurem
    647,  # Keldeo
    648,  # Meloetta
    649,  # Genesect
    716,  # Xerneas
    717,  # Yveltal
    718,  # Zygarde
    719,  # Diancie
    720,  # Hoopa
    721,  # Volcanion
    772,  # Type: Null
    773,  # Silvally
    785,  # Tapu Koko
    786,  # Tapu Lele
    787,  # Tapu Bulu
    788,  # Tapu Fini
    789,  # Cosmog
    790,  # Cosmoem
    791,  # Solgaleo
    792,  # Lunala
    800,  # Necrozma
    801,  # Magearna
    802,  # Marshadow
    807,  # Zeraora
    808,  # Meltan
    809,  # Melmetal
    888,  # Zacian
    889,  # Zamazenta
    890,  # Eternatus
    891,  # Kubfu
    892,  # Urshifu
    893,  # Zarude
    894,  # Regieleki
    895,  # Regidrago
    896,  # Glastrier
    897,  # Spectrier
    898,  # Calyrex
    905,  # Enamorus
    1000, # Gholdengo
    1001, # Wo-Chien
    1002, # Chien-Pao
    1003, # Ting-Lu
    1004, # Chi-Yu
    1005, # Roaring Moon
    1006, # Iron Valiant
    1007, # Koraidon
    1008, # Miraidon
    1009, # Walking Wake
    1010, # Iron Leaves
    1011, # Dipplin
    1012, # Poltchageist
    1013, # Sinistcha
    1014, # Okidogi
    1015, # Munkidori
    1016, # Fezandipiti
    1017, # Ogerpon
    1018, # Archaludon
    1019, # Hydrapple
    1020, # Gouging Fire
    1021, # Raging Bolt
    1022, # Iron Boulder
    1023, # Iron Crown
    1024, # Terapagos
    1025, # Pecharunt
]

def marcar_pokemon_prohibits():
    """
    Marca els Pokémon de la llista com a prohibits en competitivo.
    """
    print("--- MARCANT POKÉMON PROHIBITS EN COMPETITIVO ---\n")
    
    # Primer, marquem tots els Pokémon com a no prohibits
    print("1. Marcant tots els Pokémon com a NO prohibits...")
    query_reset = {
        "script": {
            "source": "ctx._source.is_banned = false",
            "lang": "painless"
        },
        "query": {
            "match_all": {}
        }
    }
    
    try:
        response = requests.post(
            f"{ELASTIC_URL}/{INDEX_NAME}/_update_by_query",
            json=query_reset,
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            total = response.json().get('updated', 0)
            print(f"✓ {total} Pokémon marcats com a NO prohibits\n")
        else:
            print(f"⚠ Error al resetear: {response.status_code}")
    except Exception as e:
        print(f"✗ Error al resetear: {e}\n")
    
    # Ara marquem els prohibits
    print(f"2. Marcant {len(pokemon_ids_prohibits)} Pokémon com a PROHIBITS...")
    
    # Comptadors per al resum final
    marcats_exitosament = 0
    no_trobats = 0
    errors = 0
    
    for pokemon_id in pokemon_ids_prohibits:
        try:
            # Primer obtenim el Pokémon per veure si existeix
            response_get = requests.get(f"{ELASTIC_URL}/{INDEX_NAME}/_doc/{pokemon_id}")
            
            if response_get.status_code == 200:
                pokemon_data = response_get.json()['_source']
                pokemon_name = pokemon_data.get('name', 'N/A').capitalize()
                
                # Actualitzem el camp is_banned
                update_data = {
                    "doc": {
                        "is_banned": True
                    }
                }
                
                response_update = requests.post(
                    f"{ELASTIC_URL}/{INDEX_NAME}/_update/{pokemon_id}",
                    json=update_data,
                    headers={"Content-Type": "application/json"}
                )
                
                if response_update.status_code == 200:
                    print(f"  ✓ {pokemon_name} (ID: {pokemon_id}) marcat com a PROHIBIT")
                    marcats_exitosament += 1
                else:
                    print(f"  ✗ Error actualitzant {pokemon_name} (ID: {pokemon_id}): {response_update.status_code}")
                    errors += 1
            else:
                print(f"  ⚠ Pokémon ID {pokemon_id} no trobat a la base de dades")
                no_trobats += 1
        
        except Exception as e:
            print(f"  ✗ Error processant Pokémon ID {pokemon_id}: {e}")
            errors += 1
    
    # Mostrem un resum clar
    print(f"\n--- PROCÉS FINALITZAT ---")
    print(f"✓ Pokémon prohibits marcats exitosament: {marcats_exitosament}")
    if no_trobats > 0:
        print(f"⚠ Pokémon no trobats a la BD: {no_trobats}")
    if errors > 0:
        print(f"✗ Errors durant el procés: {errors}")
    
    # Esperem una mica perquè Elasticsearch indexi els canvis
    time.sleep(1)
    
    # Verificació final: comptem quants hi ha realment a la BD
    try:
        response_count = requests.get(f"{ELASTIC_URL}/{INDEX_NAME}/_search", json={
            "query": {"term": {"is_banned": True}},
            "size": 0
        })
        if response_count.status_code == 200:
            total_banned_bd = response_count.json()['hits']['total']['value']
            print(f"✓ Total de Pokémon prohibits a la BD: {total_banned_bd}")
    except:
        pass

if __name__ == "__main__":
    marcar_pokemon_prohibits()

