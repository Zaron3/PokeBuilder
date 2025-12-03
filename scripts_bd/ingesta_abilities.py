import requests
import json
import time

# --- Configuració ---
# L'adreça de la nostra base de dades local
ELASTIC_URL = "http://localhost:9200"
# L'adreça base de l'API pública de Pokémon per a habilitats
POKEAPI_ABILITIES_URL = "https://pokeapi.co/api/v2/ability"

# Definim l'índex d'Elasticsearch on guardarem les habilitats
INDEX_NAME = "abilities"

def importar_habilitats():
    """
    Script principal que llegeix totes les habilitats de PokéAPI i insereix a Elasticsearch.
    """
    
    print("--- INICI DE LA INGESTA D'HABILITATS DE POKÉMON ---")
    
    # Primer obtenim la llista de totes les habilitats disponibles
    try:
        # PokéAPI retorna els resultats paginats, hem de fer múltiples peticions
        all_abilities = []
        next_url = POKEAPI_ABILITIES_URL
        
        while next_url:
            print(f"Obtenint llista d'habilitats de: {next_url}")
            response_list = requests.get(next_url)
            
            if response_list.status_code != 200:
                print(f"ERROR: No s'ha pogut obtenir la llista d'habilitats. Status: {response_list.status_code}")
                break
            
            data = response_list.json()
            all_abilities.extend(data["results"])
            
            # Comprovem si hi ha una pàgina següent
            next_url = data.get("next")
            time.sleep(0.1)  # Esperem per no saturar l'API
        
        total_habilitats = len(all_abilities)
        print(f"Trobades {total_habilitats} habilitats de Pokémon a importar.\n")
        
    except requests.exceptions.RequestException as e:
        print(f"ERROR DE XARXA al obtenir la llista d'habilitats: {e}")
        return
    
    # Processem cada habilitat
    for idx, ability_entry in enumerate(all_abilities, 1):
        ability_name = ability_entry["name"]
        ability_url = ability_entry["url"]
        
        # Extreiem l'ID de l'habilitat de l'URL (ex: "https://pokeapi.co/api/v2/ability/1/" -> 1)
        ability_id = ability_url.rstrip('/').split('/')[-1]
        
        if idx % 20 == 0:
            print(f"\n[{idx}/{total_habilitats}] Processant habilitat: {ability_name.capitalize()} (ID: {ability_id})")
        
        try:
            # ==========================================================
            # 1. Obtenir dades completes de l'habilitat des de PokéAPI
            # ==========================================================
            response_ability = requests.get(ability_url)
            
            if response_ability.status_code != 200:
                print(f"ERROR: No s'ha trobat l'habilitat {ability_name}. Status: {response_ability.status_code}")
                continue
            
            data = response_ability.json()
            
            # ==========================================================
            # 2. Transformar les dades
            # ==========================================================
            # Obtenim la descripció (pot haver-hi múltiples versions, agafem la primera en anglès)
            description = ""
            effect_text = ""
            
            flavor_text_entries = data.get("flavor_text_entries", [])
            for entry in flavor_text_entries:
                if entry.get("language", {}).get("name") == "en":
                    description = entry.get("flavor_text", "").replace("\n", " ").replace("\f", " ")
                    break
            
            # Obtenim l'efecte de l'habilitat
            effect_entries = data.get("effect_entries", [])
            for entry in effect_entries:
                if entry.get("language", {}).get("name") == "en":
                    effect_text = entry.get("effect", "").replace("\n", " ").replace("\f", " ")
                    break
            
            # Obtenim la generació on va aparèixer per primera vegada
            generation = data.get("generation", {}).get("name", "unknown")
            
            # Creem el document final que inserirem
            nostra_habilitat = {
                "ability_id": int(ability_id),
                "name": ability_name,
                "description": description,
                "effect": effect_text,
                "generation": generation
            }
            
            # ==========================================================
            # 3. Inserir dades a Elasticsearch
            # ==========================================================
            url_desti = f"{ELASTIC_URL}/{INDEX_NAME}/_doc/{ability_id}"
            headers = {"Content-Type": "application/json"}
            
            response_elastic = requests.put(url_desti, data=json.dumps(nostra_habilitat), headers=headers)
            
            if response_elastic.status_code in [200, 201]:
                if idx % 20 == 0:
                    print(f"✓ ÈXIT! Habilitat {ability_name.capitalize()} inserida/actualitzada.")
            else:
                print(f"ERROR a l'inserir a Elasticsearch (ID: {ability_id}): {response_elastic.status_code}")
                print(response_elastic.text)
        
        except requests.exceptions.RequestException as e:
            print(f"ERROR DE XARXA (Habilitat {ability_name}): {e}")
            print("Comprova que Elasticsearch (localhost:9200) està funcionant.")
        
        except Exception as e:
            print(f"ERROR INESPERAT (Habilitat {ability_name}): {e}")
        
        # Esperem una estona per no saturar l'API de PokéAPI
        time.sleep(0.1)
    
    print(f"\n--- INGESTA D'HABILITATS FINALITZADA ---")
    print(f"Total d'habilitats importades: {total_habilitats}")

# --- Punt d'entrada per executar l'script ---
if __name__ == "__main__":
    importar_habilitats()

