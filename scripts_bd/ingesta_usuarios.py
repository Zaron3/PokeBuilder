import requests
import json
from datetime import datetime

# --- Configuració ---
ELASTIC_URL = "http://localhost:9200"
INDEX_NAME = "users"

# Llista d'usuaris a crear
USUARIS = [
    {
        "user_id": 1,
        "username": "jordi_bolance",
        "email": "jordi.bolance@example.com",
        "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqBWVHxkd0",  # Hash de "password123"
        "profile": {
            "full_name": "Jordi Bolance",
            "bio": "Entusiasta de Pokémon competitivo",
            "favorite_pokemon": "pikachu"
        },
        "preferences": {
            "default_format": "vgc",
            "language": "ca",
            "theme": "dark"
        }
    },
    {
        "user_id": 2,
        "username": "jordi_barnola",
        "email": "jordi.barnola@example.com",
        "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqBWVHxkd0",  # Hash de "password123"
        "profile": {
            "full_name": "Jordi Barnola",
            "bio": "Creador d'equips competitius",
            "favorite_pokemon": "charizard"
        },
        "preferences": {
            "default_format": "smogon",
            "language": "ca",
            "theme": "light"
        }
    },
    {
        "user_id": 3,
        "username": "pol_torrent",
        "email": "pol.torrent@example.com",
        "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqBWVHxkd0",  # Hash de "password123"
        "profile": {
            "full_name": "Pol Torrent",
            "bio": "Expert en formats VGC",
            "favorite_pokemon": "garchomp"
        },
        "preferences": {
            "default_format": "vgc",
            "language": "es",
            "theme": "dark"
        }
    },
    {
        "user_id": 4,
        "username": "jordi_roura",
        "email": "jordi.roura@example.com",
        "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqBWVHxkd0",  # Hash de "password123"
        "profile": {
            "full_name": "Jordi Roura",
            "bio": "Jugador professional de Pokémon",
            "favorite_pokemon": "lucario"
        },
        "preferences": {
            "default_format": "vgc",
            "language": "ca",
            "theme": "dark"
        }
    },
    {
        "user_id": 5,
        "username": "marc_cassanmagnago",
        "email": "marc.cassanmagnago@example.com",
        "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqBWVHxkd0",  # Hash de "password123"
        "profile": {
            "full_name": "Marc Cassanmagnago",
            "bio": "Entrenador de Pokémon des de 2010",
            "favorite_pokemon": "tyranitar"
        },
        "preferences": {
            "default_format": "smogon",
            "language": "es",
            "theme": "light"
        }
    }
]

def importar_usuarios():
    """
    Script que importa els usuaris predefinits a Elasticsearch.
    Si un usuari ja existeix (per user_id), l'actualitza.
    """
    
    print("--- INICI DE LA INGESTA D'USUARIS ---")
    
    # Verificar connexió amb Elasticsearch
    try:
        response = requests.get(ELASTIC_URL)
        if response.status_code != 200:
            print(f"✗ ERROR: No es pot connectar a Elasticsearch a {ELASTIC_URL}")
            print("   Assegura't que Elasticsearch està funcionant.")
            return
    except Exception as e:
        print(f"✗ ERROR de connexió amb Elasticsearch: {e}")
        return
    
    print("✓ Connexió amb Elasticsearch verificada\n")
    
    # Verificar si l'índex existeix
    try:
        response = requests.get(f"{ELASTIC_URL}/{INDEX_NAME}")
        if response.status_code != 200:
            print(f"⚠ L'índex {INDEX_NAME} no existeix. Creant-lo primer...")
            print("   Executa les comandes de crear-indexs.json per crear l'índex.")
            return
    except Exception as e:
        print(f"✗ ERROR verificant l'índex: {e}")
        return
    
    # Obtindre la data actual
    now = datetime.utcnow().isoformat() + "Z"
    
    # Processar cada usuari
    exitosos = 0
    actualitzats = 0
    creats = 0
    errors = 0
    
    for usuari in USUARIS:
        user_id = usuari["user_id"]
        username = usuari["username"]
        
        try:
            # Afegir camps de data
            usuari_complet = usuari.copy()
            usuari_complet["created_at"] = now
            usuari_complet["updated_at"] = now
            usuari_complet["is_active"] = True
            
            # Verificar si l'usuari ja existeix
            url_check = f"{ELASTIC_URL}/{INDEX_NAME}/_search"
            query_check = {
                "query": {
                    "term": {
                        "user_id": user_id
                    }
                }
            }
            
            response_check = requests.post(url_check, json=query_check, headers={"Content-Type": "application/json"})
            
            existeix = False
            doc_id = None
            
            if response_check.status_code == 200:
                hits = response_check.json().get("hits", {}).get("hits", [])
                if hits:
                    existeix = True
                    doc_id = hits[0]["_id"]
                    # Obtenir la data de creació original si existeix
                    created_at_original = hits[0].get("_source", {}).get("created_at")
                    if created_at_original:
                        usuari_complet["created_at"] = created_at_original
            
            # Si no existeix, buscar per username per veure si hi ha conflicte
            if not existeix:
                query_username = {
                    "query": {
                        "term": {
                            "username.keyword": username
                        }
                    }
                }
                response_username = requests.post(url_check, json=query_username, headers={"Content-Type": "application/json"})
                if response_username.status_code == 200:
                    hits_username = response_username.json().get("hits", {}).get("hits", [])
                    if hits_username:
                        existeix = True
                        doc_id = hits_username[0]["_id"]
                        created_at_original = hits_username[0].get("_source", {}).get("created_at")
                        if created_at_original:
                            usuari_complet["created_at"] = created_at_original
            
            # Utilitzar el user_id com a ID del document si no existeix
            if not doc_id:
                doc_id = str(user_id)
            
            # Inserir o actualitzar l'usuari
            url_desti = f"{ELASTIC_URL}/{INDEX_NAME}/_doc/{doc_id}"
            headers = {"Content-Type": "application/json"}
            
            response_elastic = requests.put(url_desti, data=json.dumps(usuari_complet), headers=headers)
            
            if response_elastic.status_code in [200, 201]:
                if existeix:
                    print(f"✓ Usuari {username} (ID: {user_id}) actualitzat correctament")
                    actualitzats += 1
                else:
                    print(f"✓ Usuari {username} (ID: {user_id}) creat correctament")
                    creats += 1
                exitosos += 1
            else:
                print(f"✗ ERROR inserint/actualitzant usuari {username} (ID: {user_id}): {response_elastic.status_code}")
                print(f"   Resposta: {response_elastic.text}")
                errors += 1
        
        except requests.exceptions.RequestException as e:
            print(f"✗ ERROR DE XARXA (Usuari {username}): {e}")
            errors += 1
        except Exception as e:
            print(f"✗ ERROR INESPERAT (Usuari {username}): {e}")
            errors += 1
    
    # Resum final
    print(f"\n--- INGESTA D'USUARIS FINALITZADA ---")
    print(f"✓ Usuaris creats: {creats}")
    print(f"✓ Usuaris actualitzats: {actualitzats}")
    print(f"✓ Total exitosos: {exitosos}")
    if errors > 0:
        print(f"✗ Errors: {errors}")

# --- Punt d'entrada per executar l'script ---
if __name__ == "__main__":
    importar_usuarios()

