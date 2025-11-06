import requests
import json
import time

# --- Configuració ---
# L'adreça de la nostra base de dades local
ELASTIC_URL = "http://localhost:9200"
# L'adreça base de l'API pública de Pokémon per a tipus
POKEAPI_TYPES_URL = "https://pokeapi.co/api/v2/type"

# Definim l'índex d'Elasticsearch on guardarem els tipus
INDEX_NAME = "types"

def importar_tipus():
    """
    Script principal que llegeix tots els tipus de PokéAPI i insereix a Elasticsearch.
    Inclou les relacions d'efectivitat (debilidades, resistencias, inmunidades).
    """
    
    print("--- INICI DE LA INGESTA DE TIPUS DE POKÉMON ---")
    
    # Primer obtenim la llista de tots els tipus disponibles
    try:
        response_list = requests.get(POKEAPI_TYPES_URL)
        if response_list.status_code != 200:
            print(f"ERROR: No s'ha pogut obtenir la llista de tipus. Status: {response_list.status_code}")
            return
        
        types_list = response_list.json()
        total_tipus = len(types_list["results"])
        print(f"Trobats {total_tipus} tipus de Pokémon a importar.\n")
        
    except requests.exceptions.RequestException as e:
        print(f"ERROR DE XARXA al obtenir la llista de tipus: {e}")
        return
    
    # Processem cada tipus
    for idx, type_entry in enumerate(types_list["results"], 1):
        type_name = type_entry["name"]
        type_url = type_entry["url"]
        
        # Extreiem l'ID del tipus de l'URL (ex: "https://pokeapi.co/api/v2/type/1/" -> 1)
        type_id = int(type_url.rstrip('/').split('/')[-1])
        
        print(f"\n[{idx}/{total_tipus}] Processant tipus: {type_name.capitalize()} (ID: {type_id})")
        
        try:
            # ==========================================================
            # 1. Obtenir dades completes del tipus des de PokéAPI
            # ==========================================================
            response_type = requests.get(type_url)
            
            if response_type.status_code != 200:
                print(f"ERROR: No s'ha trobat el tipus {type_name}. Status: {response_type.status_code}")
                continue
            
            data = response_type.json()
            
            # ==========================================================
            # 2. Transformar les dades d'efectivitat
            # ==========================================================
            # PokéAPI retorna les relacions en "damage_relations"
            damage_relations = data.get("damage_relations", {})
            
            # Tipus que fan doble dany a aquest tipus (debilidades)
            double_damage_from = [t["name"] for t in damage_relations.get("double_damage_from", [])]
            
            # Tipus que fan mig dany a aquest tipus (resistencias)
            half_damage_from = [t["name"] for t in damage_relations.get("half_damage_from", [])]
            
            # Tipus que no fan dany a aquest tipus (inmunidades)
            no_damage_from = [t["name"] for t in damage_relations.get("no_damage_from", [])]
            
            # Tipus als quals aquest tipus fa doble dany (fortalezas)
            double_damage_to = [t["name"] for t in damage_relations.get("double_damage_to", [])]
            
            # Tipus als quals aquest tipus fa mig dany
            half_damage_to = [t["name"] for t in damage_relations.get("half_damage_to", [])]
            
            # Tipus als quals aquest tipus no fa dany
            no_damage_to = [t["name"] for t in damage_relations.get("no_damage_to", [])]
            
            # Creem el document final que inserirem
            nostre_tipus = {
                "type_id": type_id,
                "name": type_name,
                "double_damage_from": double_damage_from,
                "half_damage_from": half_damage_from,
                "no_damage_from": no_damage_from,
                "double_damage_to": double_damage_to,
                "half_damage_to": half_damage_to,
                "no_damage_to": no_damage_to
            }
            
            # ==========================================================
            # 3. Inserir dades a Elasticsearch
            # ==========================================================
            url_desti = f"{ELASTIC_URL}/{INDEX_NAME}/_doc/{type_id}"
            headers = {"Content-Type": "application/json"}
            
            response_elastic = requests.put(url_desti, data=json.dumps(nostre_tipus), headers=headers)
            
            if response_elastic.status_code in [200, 201]:
                print(f"✓ ÈXIT! Tipus {type_name.capitalize()} inserit/actualitzat.")
                print(f"  - Dèbils contra: {', '.join(double_damage_from) if double_damage_from else 'cap'}")
                print(f"  - Resistents a: {', '.join(half_damage_from) if half_damage_from else 'cap'}")
                print(f"  - Inmunes a: {', '.join(no_damage_from) if no_damage_from else 'cap'}")
                print(f"  - Efectius contra: {', '.join(double_damage_to) if double_damage_to else 'cap'}")
            else:
                print(f"ERROR a l'inserir a Elasticsearch (ID: {type_id}): {response_elastic.status_code}")
                print(response_elastic.text)
        
        except requests.exceptions.RequestException as e:
            print(f"ERROR DE XARXA (Tipus {type_name}): {e}")
            print("Comprova que Elasticsearch (localhost:9200) està funcionant.")
        
        except Exception as e:
            print(f"ERROR INESPERAT (Tipus {type_name}): {e}")
        
        # Esperem una estona per no saturar l'API de PokéAPI
        time.sleep(0.1)
    
    print("\n--- INGESTA DE TIPUS FINALITZADA ---")
    print(f"Total de tipus importats: {total_tipus}")

# --- Punt d'entrada per executar l'script ---
if __name__ == "__main__":
    importar_tipus()

