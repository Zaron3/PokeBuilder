import requests
import json
from datetime import datetime

# --- Configuració ---
ELASTIC_URL = "http://localhost:9200"
INDEX_NAME = "teams"

# Llista d'equips a crear
EQUIPS = [
    # Equips per a l'usuari 1 (jordi_bolance)
    {
        "team_name": "Equip de Sol VGC",
        "description": "Equip VGC basat en Sol (Torkoal + Lilligant-Hisui)",
        "user_id": 1,
        "format": "VGC Reg G",
        "team_members": [
            {
                "base_pokemon": "Torkoal",
                "nickname": "Volcano",
                "item": "Charcoal",
                "ability": "Drought",
                "tera_type": "Fire",
                "nature": "Quiet",
                "moves": ["Eruption", "Heat Wave", "Protect", "Earth Power"],
                "evs": {
                    "hp": 252,
                    "attack": 0,
                    "defense": 0,
                    "sp_atk": 252,
                    "sp_def": 4,
                    "speed": 0
                }
            },
            {
                "base_pokemon": "Lilligant-Hisui",
                "item": "Focus Sash",
                "ability": "Chlorophyll",
                "tera_type": "Fighting",
                "nature": "Jolly",
                "moves": ["Solar Blade", "Close Combat", "After You", "Protect"],
                "evs": {
                    "hp": 4,
                    "attack": 252,
                    "defense": 0,
                    "sp_atk": 0,
                    "sp_def": 0,
                    "speed": 252
                }
            },
            {
                "base_pokemon": "Flutter Mane",
                "item": "Booster Energy",
                "ability": "Protosynthesis",
                "tera_type": "Fairy",
                "nature": "Timid",
                "moves": ["Moonblast", "Shadow Ball", "Dazzling Gleam", "Protect"],
                "evs": {
                    "hp": 4,
                    "attack": 0,
                    "defense": 0,
                    "sp_atk": 252,
                    "sp_def": 0,
                    "speed": 252
                }
            },
            {
                "base_pokemon": "Incineroar",
                "item": "Sitrus Berry",
                "ability": "Intimidate",
                "tera_type": "Grass",
                "nature": "Careful",
                "moves": ["Flare Blitz", "Knock Off", "Fake Out", "Parting Shot"],
                "evs": {
                    "hp": 252,
                    "attack": 0,
                    "defense": 100,
                    "sp_atk": 0,
                    "sp_def": 156,
                    "speed": 0
                }
            },
            {
                "base_pokemon": "Raging Bolt",
                "item": "Assault Vest",
                "ability": "Protosynthesis",
                "tera_type": "Electric",
                "nature": "Modest",
                "moves": ["Thunderclap", "Draco Meteor", "Volt Switch", "Weather Ball"],
                "evs": {
                    "hp": 252,
                    "attack": 0,
                    "defense": 0,
                    "sp_atk": 252,
                    "sp_def": 4,
                    "speed": 0
                }
            },
            {
                "base_pokemon": "Urshifu-Rapid-Strike",
                "item": "Mystic Water",
                "ability": "Unseen Fist",
                "tera_type": "Water",
                "nature": "Jolly",
                "moves": ["Surging Strikes", "Close Combat", "Aqua Jet", "Protect"],
                "evs": {
                    "hp": 4,
                    "attack": 252,
                    "defense": 0,
                    "sp_atk": 0,
                    "sp_def": 0,
                    "speed": 252
                }
            }
        ]
    },
    {
        "team_name": "Equip Offensiu OU",
        "description": "Equip ofensiu per a Smogon OU",
        "user_id": 1,
        "format": "OU",
        "team_members": [
            {
                "base_pokemon": "Garchomp",
                "nickname": "Chomper",
                "item": "Rocky Helmet",
                "ability": "Rough Skin",
                "tera_type": "Ground",
                "nature": "Jolly",
                "moves": ["Earthquake", "Dragon Claw", "Stone Edge", "Swords Dance"],
                "evs": {
                    "hp": 0,
                    "attack": 252,
                    "defense": 0,
                    "sp_atk": 0,
                    "sp_def": 4,
                    "speed": 252
                }
            },
            {
                "base_pokemon": "Rotom-Wash",
                "item": "Leftovers",
                "ability": "Levitate",
                "tera_type": "Electric",
                "nature": "Bold",
                "moves": ["Volt Switch", "Hydro Pump", "Will-O-Wisp", "Pain Split"],
                "evs": {
                    "hp": 252,
                    "attack": 0,
                    "defense": 252,
                    "sp_atk": 0,
                    "sp_def": 4,
                    "speed": 0
                }
            },
            {
                "base_pokemon": "Heatran",
                "item": "Air Balloon",
                "ability": "Flash Fire",
                "tera_type": "Fire",
                "nature": "Modest",
                "moves": ["Magma Storm", "Earth Power", "Flash Cannon", "Stealth Rock"],
                "evs": {
                    "hp": 252,
                    "attack": 0,
                    "defense": 0,
                    "sp_atk": 252,
                    "sp_def": 4,
                    "speed": 0
                }
            }
        ]
    },
    # Equips per a l'usuari 2 (jordi_barnola)
    {
        "team_name": "Equip Balance VGC",
        "description": "Equip balancejat per a VGC Reg G",
        "user_id": 2,
        "format": "VGC Reg G",
        "team_members": [
            {
                "base_pokemon": "Ogerpon-Wellspring",
                "item": "Wellspring Mask",
                "ability": "Water Absorb",
                "tera_type": "Water",
                "nature": "Jolly",
                "moves": ["Ivy Cudgel", "Horn Leech", "Follow Me", "Spiky Shield"],
                "evs": {
                    "hp": 252,
                    "attack": 252,
                    "defense": 0,
                    "sp_atk": 0,
                    "sp_def": 4,
                    "speed": 0
                }
            },
            {
                "base_pokemon": "Landorus-Therian",
                "item": "Choice Scarf",
                "ability": "Intimidate",
                "tera_type": "Flying",
                "nature": "Jolly",
                "moves": ["Earthquake", "U-turn", "Rock Slide", "Fly"],
                "evs": {
                    "hp": 0,
                    "attack": 252,
                    "defense": 0,
                    "sp_atk": 0,
                    "sp_def": 4,
                    "speed": 252
                }
            },
            {
                "base_pokemon": "Amoonguss",
                "item": "Sitrus Berry",
                "ability": "Regenerator",
                "tera_type": "Water",
                "nature": "Relaxed",
                "moves": ["Spore", "Rage Powder", "Pollen Puff", "Protect"],
                "evs": {
                    "hp": 252,
                    "attack": 0,
                    "defense": 252,
                    "sp_atk": 0,
                    "sp_def": 4,
                    "speed": 0
                }
            },
            {
                "base_pokemon": "Chi-Yu",
                "item": "Focus Sash",
                "ability": "Beads of Ruin",
                "tera_type": "Ghost",
                "nature": "Timid",
                "moves": ["Dark Pulse", "Flamethrower", "Nasty Plot", "Protect"],
                "evs": {
                    "hp": 4,
                    "attack": 0,
                    "defense": 0,
                    "sp_atk": 252,
                    "sp_def": 0,
                    "speed": 252
                }
            },
            {
                "base_pokemon": "Iron Hands",
                "item": "Assault Vest",
                "ability": "Quark Drive",
                "tera_type": "Fighting",
                "nature": "Adamant",
                "moves": ["Drain Punch", "Thunder Punch", "Ice Punch", "Volt Switch"],
                "evs": {
                    "hp": 252,
                    "attack": 252,
                    "defense": 0,
                    "sp_atk": 0,
                    "sp_def": 4,
                    "speed": 0
                }
            },
            {
                "base_pokemon": "Tornadus",
                "item": "Covert Cloak",
                "ability": "Prankster",
                "tera_type": "Flying",
                "nature": "Timid",
                "moves": ["Tailwind", "Bleakwind Storm", "Taunt", "Protect"],
                "evs": {
                    "hp": 252,
                    "attack": 0,
                    "defense": 0,
                    "sp_atk": 0,
                    "sp_def": 4,
                    "speed": 252
                }
            }
        ]
    },
    {
        "team_name": "Equip Rain OU",
        "description": "Equip basat en pluja per a Smogon OU",
        "user_id": 2,
        "format": "OU",
        "team_members": [
            {
                "base_pokemon": "Pelipper",
                "item": "Damp Rock",
                "ability": "Drizzle",
                "tera_type": "Water",
                "nature": "Bold",
                "moves": ["Hurricane", "Scald", "U-turn", "Roost"],
                "evs": {
                    "hp": 252,
                    "attack": 0,
                    "defense": 252,
                    "sp_atk": 0,
                    "sp_def": 4,
                    "speed": 0
                }
            },
            {
                "base_pokemon": "Barraskewda",
                "item": "Choice Band",
                "ability": "Swift Swim",
                "tera_type": "Water",
                "nature": "Adamant",
                "moves": ["Liquidation", "Close Combat", "Psychic Fangs", "Flip Turn"],
                "evs": {
                    "hp": 0,
                    "attack": 252,
                    "defense": 0,
                    "sp_atk": 0,
                    "sp_def": 4,
                    "speed": 252
                }
            },
            {
                "base_pokemon": "Kingdra",
                "item": "Life Orb",
                "ability": "Swift Swim",
                "tera_type": "Water",
                "nature": "Modest",
                "moves": ["Hydro Pump", "Draco Meteor", "Hurricane", "Ice Beam"],
                "evs": {
                    "hp": 0,
                    "attack": 0,
                    "defense": 0,
                    "sp_atk": 252,
                    "sp_def": 4,
                    "speed": 252
                }
            }
        ]
    }
]

def importar_teams():
    """
    Script que importa els equips predefinits a Elasticsearch.
    Si un equip ja existeix (per team_name i user_id), l'actualitza.
    """
    
    print("--- INICI DE LA INGESTA D'EQUIPS ---")
    
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
    
    # Processar cada equip
    exitosos = 0
    actualitzats = 0
    creats = 0
    errors = 0
    
    for idx, equip in enumerate(EQUIPS, 1):
        user_id = equip["user_id"]
        team_name = equip["team_name"]
        
        try:
            # Verificar si l'equip ja existeix (per team_name i user_id)
            url_check = f"{ELASTIC_URL}/{INDEX_NAME}/_search"
            query_check = {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"team_name.keyword": team_name}},
                            {"term": {"user_id": str(user_id)}}
                        ]
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
            
            # Si no existeix, generar un ID únic basat en user_id i índex
            if not doc_id:
                doc_id = f"team_user{user_id}_{idx}"
            
            # Inserir o actualitzar l'equip
            url_desti = f"{ELASTIC_URL}/{INDEX_NAME}/_doc/{doc_id}"
            headers = {"Content-Type": "application/json"}
            
            # Convertir user_id a string perquè el mapping és keyword
            equip_actualitzat = equip.copy()
            equip_actualitzat["user_id"] = str(user_id)
            
            response_elastic = requests.put(url_desti, data=json.dumps(equip_actualitzat), headers=headers)
            
            if response_elastic.status_code in [200, 201]:
                if existeix:
                    print(f"✓ Equip '{team_name}' (Usuari {user_id}) actualitzat correctament")
                    actualitzats += 1
                else:
                    print(f"✓ Equip '{team_name}' (Usuari {user_id}) creat correctament")
                    creats += 1
                exitosos += 1
            else:
                print(f"✗ ERROR inserint/actualitzant equip '{team_name}' (Usuari {user_id}): {response_elastic.status_code}")
                print(f"   Resposta: {response_elastic.text}")
                errors += 1
        
        except requests.exceptions.RequestException as e:
            print(f"✗ ERROR DE XARXA (Equip '{team_name}'): {e}")
            errors += 1
        except Exception as e:
            print(f"✗ ERROR INESPERAT (Equip '{team_name}'): {e}")
            errors += 1
    
    # Resum final
    print(f"\n--- INGESTA D'EQUIPS FINALITZADA ---")
    print(f"✓ Equips creats: {creats}")
    print(f"✓ Equips actualitzats: {actualitzats}")
    print(f"✓ Total exitosos: {exitosos}")
    if errors > 0:
        print(f"✗ Errors: {errors}")

# --- Punt d'entrada per executar l'script ---
if __name__ == "__main__":
    importar_teams()

