import requests
import json
import time

# --- Configuració ---
# L'adreça de la nostra base de dades local
ELASTIC_URL = "http://localhost:9200"
# L'adreça base de l'API pública de Pokémon per a naturalezas
POKEAPI_NATURES_URL = "https://pokeapi.co/api/v2/nature"

# Definim l'índex d'Elasticsearch on guardarem les naturalezas
INDEX_NAME = "natures"

def importar_naturalezas():
    """
    Script principal que llegeix totes les naturalezas de PokéAPI i insereix a Elasticsearch.
    """
    
    print("--- INICI DE LA INGESTA DE NATURALEZAS DE POKÉMON ---")
    
    # Primer obtenim la llista de totes les naturalezas disponibles
    try:
        # PokéAPI retorna els resultats paginats, hem de fer múltiples peticions
        all_natures = []
        next_url = POKEAPI_NATURES_URL
        
        while next_url:
            print(f"Obtenint llista de naturalezas de: {next_url}")
            response_list = requests.get(next_url)
            
            if response_list.status_code != 200:
                print(f"ERROR: No s'ha pogut obtenir la llista de naturalezas. Status: {response_list.status_code}")
                break
            
            data = response_list.json()
            all_natures.extend(data["results"])
            
            # Comprovem si hi ha una pàgina següent
            next_url = data.get("next")
            time.sleep(0.1)  # Esperem per no saturar l'API
        
        total_naturalezas = len(all_natures)
        print(f"Trobades {total_naturalezas} naturalezas de Pokémon a importar.\n")
        
    except requests.exceptions.RequestException as e:
        print(f"ERROR DE XARXA al obtenir la llista de naturalezas: {e}")
        return
    
    # Processem cada naturalesa
    for idx, nature_entry in enumerate(all_natures, 1):
        nature_name = nature_entry["name"]
        nature_url = nature_entry["url"]
        
        # Extreiem l'ID de la naturalesa de l'URL (ex: "https://pokeapi.co/api/v2/nature/1/" -> 1)
        nature_id = nature_url.rstrip('/').split('/')[-1]
        
        print(f"[{idx}/{total_naturalezas}] Processant naturalesa: {nature_name.capitalize()} (ID: {nature_id})")
        
        try:
            # ==========================================================
            # 1. Obtenir dades completes de la naturalesa des de PokéAPI
            # ==========================================================
            response_nature = requests.get(nature_url)
            
            if response_nature.status_code != 200:
                print(f"ERROR: No s'ha trobat la naturalesa {nature_name}. Status: {response_nature.status_code}")
                continue
            
            data = response_nature.json()
            
            # ==========================================================
            # 2. Transformar les dades
            # ==========================================================
            # Obtenim l'estadística que augmenta
            increased_stat = None
            if data.get("increased_stat"):
                increased_stat = data["increased_stat"].get("name")
            
            # Obtenim l'estadística que disminueix
            decreased_stat = None
            if data.get("decreased_stat"):
                decreased_stat = data["decreased_stat"].get("name")
            
            # Obtenim el sabor que li agrada (per a Poffins/berries)
            likes_flavor = None
            if data.get("likes_flavor"):
                likes_flavor = data["likes_flavor"].get("name")
            
            # Obtenim el sabor que odia (per a Poffins/berries)
            hates_flavor = None
            if data.get("hates_flavor"):
                hates_flavor = data["hates_flavor"].get("name")
            
            # Creem el document final que inserirem
            nostra_naturalesa = {
                "nature_id": int(nature_id),
                "name": nature_name,
                "increased_stat": increased_stat,
                "decreased_stat": decreased_stat,
                "likes_flavor": likes_flavor,
                "hates_flavor": hates_flavor
            }
            
            # ==========================================================
            # 3. Inserir dades a Elasticsearch
            # ==========================================================
            url_desti = f"{ELASTIC_URL}/{INDEX_NAME}/_doc/{nature_id}"
            headers = {"Content-Type": "application/json"}
            
            response_elastic = requests.put(url_desti, data=json.dumps(nostra_naturalesa), headers=headers)
            
            if response_elastic.status_code in [200, 201]:
                stat_info = ""
                if increased_stat and decreased_stat:
                    stat_info = f" (+{increased_stat}, -{decreased_stat})"
                elif not increased_stat and not decreased_stat:
                    stat_info = " (neutral)"
                print(f"✓ ÈXIT! Naturalesa {nature_name.capitalize()}{stat_info} inserida/actualitzada.")
            else:
                print(f"ERROR a l'inserir a Elasticsearch (ID: {nature_id}): {response_elastic.status_code}")
                print(response_elastic.text)
        
        except requests.exceptions.RequestException as e:
            print(f"ERROR DE XARXA (Naturalesa {nature_name}): {e}")
            print("Comprova que Elasticsearch (localhost:9200) està funcionant.")
        
        except Exception as e:
            print(f"ERROR INESPERAT (Naturalesa {nature_name}): {e}")
        
        # Esperem una estona per no saturar l'API de PokéAPI
        time.sleep(0.1)
    
    print(f"\n--- INGESTA DE NATURALEZAS FINALITZADA ---")
    print(f"Total de naturalezas importades: {total_naturalezas}")

# --- Punt d'entrada per executar l'script ---
if __name__ == "__main__":
    importar_naturalezas()

