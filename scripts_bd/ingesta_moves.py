import requests
import json
import time

# --- Configuració ---
# L'adreça de la nostra base de dades local
ELASTIC_URL = "http://localhost:9200"
# L'adreça base de l'API pública de Pokémon per a moviments
POKEAPI_MOVES_URL = "https://pokeapi.co/api/v2/move"

# Definim l'índex d'Elasticsearch on guardarem els moviments
INDEX_NAME = "moves"

def importar_moviments():
    """
    Script principal que llegeix tots els moviments de PokéAPI i insereix a Elasticsearch.
    """
    
    print("--- INICI DE LA INGESTA DE MOVIMENTS DE POKÉMON ---")
    
    # Primer obtenim la llista de tots els moviments disponibles
    try:
        # PokéAPI retorna els resultats paginats, hem de fer múltiples peticions
        # Començarem amb la primera pàgina
        all_moves = []
        next_url = POKEAPI_MOVES_URL
        
        while next_url:
            print(f"Obtenint llista de moviments de: {next_url}")
            response_list = requests.get(next_url)
            
            if response_list.status_code != 200:
                print(f"ERROR: No s'ha pogut obtenir la llista de moviments. Status: {response_list.status_code}")
                break
            
            data = response_list.json()
            all_moves.extend(data["results"])
            
            # Comprovem si hi ha una pàgina següent
            next_url = data.get("next")
            time.sleep(0.1)  # Esperem per no saturar l'API
        
        total_moviments = len(all_moves)
        print(f"Trobats {total_moviments} moviments de Pokémon a importar.\n")
        
    except requests.exceptions.RequestException as e:
        print(f"ERROR DE XARXA al obtenir la llista de moviments: {e}")
        return
    
    # Processem cada moviment
    for idx, move_entry in enumerate(all_moves, 1):
        move_name = move_entry["name"]
        move_url = move_entry["url"]
        
        # Extreiem l'ID del moviment de l'URL (ex: "https://pokeapi.co/api/v2/move/1/" -> 1)
        move_id = move_url.rstrip('/').split('/')[-1]
        
        if idx % 50 == 0:
            print(f"\n[{idx}/{total_moviments}] Processant moviment: {move_name.capitalize()} (ID: {move_id})")
        
        try:
            # ==========================================================
            # 1. Obtenir dades completes del moviment des de PokéAPI
            # ==========================================================
            response_move = requests.get(move_url)
            
            if response_move.status_code != 200:
                print(f"ERROR: No s'ha trobat el moviment {move_name}. Status: {response_move.status_code}")
                continue
            
            data = response_move.json()
            
            # ==========================================================
            # 2. Transformar les dades
            # ==========================================================
            # Obtenim el tipus del moviment
            move_type = data.get("type", {}).get("name", "unknown")
            
            # Obtenim la categoria (damage_class): physical, special, o status
            damage_class = data.get("damage_class", {}).get("name", "status")
            # Traduïm a l'anglès per consistència
            category_map = {
                "physical": "physical",
                "special": "special",
                "status": "status"
            }
            category = category_map.get(damage_class, "status")
            
            # Obtenim poder, precisió i PP
            power = data.get("power")
            accuracy = data.get("accuracy")
            pp = data.get("pp")
            
            # Obtenim la descripció (pot haver-hi múltiples versions, agafem la primera en anglès)
            description = ""
            flavor_text_entries = data.get("flavor_text_entries", [])
            for entry in flavor_text_entries:
                if entry.get("language", {}).get("name") == "en":
                    description = entry.get("flavor_text", "").replace("\n", " ").replace("\f", " ")
                    break
            
            # Si no hi ha descripció en anglès, agafem la primera disponible
            if not description and flavor_text_entries:
                description = flavor_text_entries[0].get("flavor_text", "").replace("\n", " ").replace("\f", " ")
            
            # Creem el document final que inserirem
            nostre_moviment = {
                "move_id": move_id,
                "name": move_name,
                "type": move_type,
                "category": category,
                "power": power if power is not None else 0,
                "accuracy": accuracy if accuracy is not None else 0,
                "pp": pp if pp is not None else 0,
                "description": description
            }
            
            # ==========================================================
            # 3. Inserir dades a Elasticsearch
            # ==========================================================
            url_desti = f"{ELASTIC_URL}/{INDEX_NAME}/_doc/{move_id}"
            headers = {"Content-Type": "application/json"}
            
            response_elastic = requests.put(url_desti, data=json.dumps(nostre_moviment), headers=headers)
            
            if response_elastic.status_code in [200, 201]:
                if idx % 50 == 0:
                    print(f"✓ ÈXIT! Moviment {move_name.capitalize()} inserit/actualitzat.")
            else:
                print(f"ERROR a l'inserir a Elasticsearch (ID: {move_id}): {response_elastic.status_code}")
                print(response_elastic.text)
        
        except requests.exceptions.RequestException as e:
            print(f"ERROR DE XARXA (Moviment {move_name}): {e}")
            print("Comprova que Elasticsearch (localhost:9200) està funcionant.")
        
        except Exception as e:
            print(f"ERROR INESPERAT (Moviment {move_name}): {e}")
        
        # Esperem una estona per no saturar l'API de PokéAPI
        time.sleep(0.1)
    
    print(f"\n--- INGESTA DE MOVIMENTS FINALITZADA ---")
    print(f"Total de moviments importats: {total_moviments}")

# --- Punt d'entrada per executar l'script ---
if __name__ == "__main__":
    importar_moviments()

