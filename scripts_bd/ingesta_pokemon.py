import requests
import json
import time

# --- Configuració ---
# L'adreça de la nostra base de dades local
ELASTIC_URL = "http://localhost:9200"
# L'adreça base de l'API pública de Pokémon
POKEAPI_BASE_URL = "https://pokeapi.co/api/v2/pokemon"

# Definim l'índex d'Elasticsearch on guardarem els Pokémon
INDEX_NAME = "pokemon"

def importar_pokemons():
    """
    Script principal que llegeix de PokéAPI i insereix a Elasticsearch.
    """
    
    # IDs dels Pokémon que volem importar (de l'1 al 1026)
    ids_a_importar = range(1, 1026) # range(1, 10) va de 1 a 9
    
    print(f"--- INICI DE LA INGESTA DE {len(ids_a_importar)} POKÉMONS ---")
    
    for pokemon_id in ids_a_importar:
        
        print(f"\n--- Processant Pokémon ID: {pokemon_id} ---")
        
        try:
            # ==========================================================
            # 1. Obtenir dades de PokéAPI
            # ==========================================================
            url_pokeapi = f"{POKEAPI_BASE_URL}/{pokemon_id}"
            response_pokeapi = requests.get(url_pokeapi)
            
            # Comprovem si la petició a PokéAPI ha anat bé
            if response_pokeapi.status_code != 200:
                print(f"ERROR a PokéAPI: No s'ha trobat el Pokémon ID {pokemon_id}. Status: {response_pokeapi.status_code}")
                continue # Saltem al següent Pokémon
                
            data = response_pokeapi.json()
            
            # ==========================================================
            # 2. Transformar les dades (La part clau!)
            # ==========================================================
            # Aquesta estructura HA DE COINCIDIR amb el vostre MAPPING
            print(f"Transformant dades per a: {data['name'].capitalize()}...")

            # Creem la llista de tipus (ex: ["grass", "poison"])
            # El vostre mapping deia "types": { "type": "keyword" }, que sol implicar una llista.
            tipus_pokemon = [t["type"]["name"] for t in data["types"]]
            
            # Creem l'objecte de stats (ex: {"hp": 45, "attack": 49, ...})
            # El vostre mapping deia "stats": { "properties": { "hp": ... } }
            stats_pokemon = {}
            for s in data["stats"]:
                # Canviem "special-attack" per "special_attack" per si el mapping ho té així
                stat_name = s["stat"]["name"].replace("-", "_") 
                stats_pokemon[stat_name] = s["base_stat"]
            
            # Creem la llista d'habilitats (nested structure)
            abilities_pokemon = []
            for ability in data.get("abilities", []):
                abilities_pokemon.append({
                    "name": ability["ability"]["name"],
                    "is_hidden": ability.get("is_hidden", False)
                })
            
            # Creem la llista de moviments disponibles (moves_pool)
            # PokéAPI retorna molts moviments amb diferents mètodes d'aprenentatge
            moves_pool_pokemon = []
            for move_entry in data.get("moves", []):
                move_name = move_entry["move"]["name"]
                # Agafem el primer mètode d'aprenentatge (normalment hi ha un principal)
                # Per simplificar, agafem el primer "version_group_details"
                learn_method = None
                if move_entry.get("version_group_details"):
                    # Agafem el mètode del primer grup de versions
                    learn_method = move_entry["version_group_details"][0]["move_learn_method"]["name"]
                
                if learn_method:
                    moves_pool_pokemon.append({
                        "name": move_name,
                        "learn_method": learn_method
                    })
            
            # Creem el document final que inserirem
            # Nota: is_banned per defecte és false. Es pot actualitzar després amb un script específic
            nostre_pokemon = {
                "pokedex_id": data["id"],
                "name": data["name"],
                "types": tipus_pokemon,
                "stats": stats_pokemon,
                "abilities": abilities_pokemon,
                "moves_pool": moves_pool_pokemon,
                "is_banned": False  # Per defecte no està prohibit. Es pot actualitzar després
            }

            # ==========================================================
            # 3. Inserir dades a Elasticsearch
            # ==========================================================
            
            # Fem servir l'ID de la Pokédex com a ID del document a Elasticsearch
            # L'índex és 'pokemon', el tipus '_doc', i l'ID és el de la Pokédex
            url_desti = f"{ELASTIC_URL}/{INDEX_NAME}/_doc/{pokemon_id}"
            
            headers = {"Content-Type": "application/json"}
            
            # Fem un 'PUT' per posar-li nosaltres l'ID.
            # Si el document ja existeix, el sobreescriu.
            response_elastic = requests.put(url_desti, data=json.dumps(nostre_pokemon), headers=headers)

            # Comprovem la resposta d'Elasticsearch
            # 201 = Creat (Created)
            # 200 = Actualitzat (OK)
            if response_elastic.status_code == 201:
                print(f"ÈXIT! Pokémon {nostre_pokemon['name'].capitalize()} (ID: {pokemon_id}) inserit a Elasticsearch.")
            elif response_elastic.status_code == 200:
                print(f"ÈXIT! Pokémon {nostre_pokemon['name'].capitalize()} (ID: {pokemon_id}) actualitzat a Elasticsearch.")
            else:
                print(f"ERROR a l'inserir a Elasticsearch (ID: {pokemon_id}): {response_elastic.status_code}")
                print(response_elastic.text)
        
        except requests.exceptions.RequestException as e:
            print(f"ERROR DE XARXA (ID: {pokemon_id}): {e}")
            print("Comprova que Elasticsearch (localhost:9200) està funcionant.")
            
        # Esperem una estona per no saturar l'API de PokéAPI
        time.sleep(0.1) 

    print("\n--- INGESTA FINALITZADA ---")

# --- Punt d'entrada per executar l'script ---
if __name__ == "__main__":
    importar_pokemons()

