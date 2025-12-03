import requests
import json
import time

# --- Configuració ---
# L'adreça de la nostra base de dades local
ELASTIC_URL = "http://localhost:9200"
# L'adreça base de l'API pública de Pokémon per a items
POKEAPI_ITEMS_URL = "https://pokeapi.co/api/v2/item"

# Definim l'índex d'Elasticsearch on guardarem els items
INDEX_NAME = "items"

def importar_items():
    """
    Script principal que llegeix tots els items de PokéAPI i insereix a Elasticsearch.
    """
    
    print("--- INICI DE LA INGESTA D'ITEMS DE POKÉMON ---")
    
    # Primer obtenim la llista de tots els items disponibles
    try:
        # PokéAPI retorna els resultats paginats, hem de fer múltiples peticions
        all_items = []
        next_url = POKEAPI_ITEMS_URL
        
        while next_url:
            print(f"Obtenint llista d'items de: {next_url}")
            response_list = requests.get(next_url)
            
            if response_list.status_code != 200:
                print(f"ERROR: No s'ha pogut obtenir la llista d'items. Status: {response_list.status_code}")
                break
            
            data = response_list.json()
            all_items.extend(data["results"])
            
            # Comprovem si hi ha una pàgina següent
            next_url = data.get("next")
            time.sleep(0.1)  # Esperem per no saturar l'API
        
        total_items = len(all_items)
        print(f"Trobats {total_items} items de Pokémon a importar.\n")
        
    except requests.exceptions.RequestException as e:
        print(f"ERROR DE XARXA al obtenir la llista d'items: {e}")
        return
    
    # Processem cada item
    for idx, item_entry in enumerate(all_items, 1):
        item_name = item_entry["name"]
        item_url = item_entry["url"]
        
        # Extreiem l'ID de l'item de l'URL (ex: "https://pokeapi.co/api/v2/item/1/" -> 1)
        item_id = item_url.rstrip('/').split('/')[-1]
        
        if idx % 50 == 0:
            print(f"\n[{idx}/{total_items}] Processant item: {item_name.capitalize()} (ID: {item_id})")
        
        try:
            # ==========================================================
            # 1. Obtenir dades completes de l'item des de PokéAPI
            # ==========================================================
            response_item = requests.get(item_url)
            
            if response_item.status_code != 200:
                print(f"ERROR: No s'ha trobat l'item {item_name}. Status: {response_item.status_code}")
                continue
            
            data = response_item.json()
            
            # ==========================================================
            # 2. Transformar les dades
            # ==========================================================
            # Obtenim la categoria
            category = data.get("category", {}).get("name", "unknown")
            
            # Obtenim el cost
            cost = data.get("cost", 0)
            
            # Obtenim la descripció (pot haver-hi múltiples versions, agafem la primera en anglès)
            description = ""
            effect_text = ""
            flavor_text_entries = data.get("flavor_text_entries", [])
            for entry in flavor_text_entries:
                if entry.get("language", {}).get("name") == "en":
                    description = entry.get("text", "").replace("\n", " ").replace("\f", " ")
                    break
            
            # Obtenim l'efecte de l'item
            effect_entries = data.get("effect_entries", [])
            for entry in effect_entries:
                if entry.get("language", {}).get("name") == "en":
                    effect_text = entry.get("effect", "").replace("\n", " ").replace("\f", " ")
                    break
            
            # Obtenim atributs (ex: "holdable", "consumable", etc.)
            attributes = []
            for attr in data.get("attributes", []):
                attributes.append(attr.get("name", ""))
            
            # Creem el document final que inserirem
            nostre_item = {
                "item_id": int(item_id),
                "name": item_name,
                "category": category,
                "cost": cost,
                "description": description,
                "effect": effect_text,
                "attributes": attributes
            }
            
            # ==========================================================
            # 3. Inserir dades a Elasticsearch
            # ==========================================================
            url_desti = f"{ELASTIC_URL}/{INDEX_NAME}/_doc/{item_id}"
            headers = {"Content-Type": "application/json"}
            
            response_elastic = requests.put(url_desti, data=json.dumps(nostre_item), headers=headers)
            
            if response_elastic.status_code in [200, 201]:
                if idx % 50 == 0:
                    print(f"✓ ÈXIT! Item {item_name.capitalize()} inserit/actualitzat.")
            else:
                print(f"ERROR a l'inserir a Elasticsearch (ID: {item_id}): {response_elastic.status_code}")
                print(response_elastic.text)
        
        except requests.exceptions.RequestException as e:
            print(f"ERROR DE XARXA (Item {item_name}): {e}")
            print("Comprova que Elasticsearch (localhost:9200) està funcionant.")
        
        except Exception as e:
            print(f"ERROR INESPERAT (Item {item_name}): {e}")
        
        # Esperem una estona per no saturar l'API de PokéAPI
        time.sleep(0.1)
    
    print(f"\n--- INGESTA D'ITEMS FINALITZADA ---")
    print(f"Total d'items importats: {total_items}")

# --- Punt d'entrada per executar l'script ---
if __name__ == "__main__":
    importar_items()

