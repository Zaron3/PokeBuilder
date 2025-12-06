

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from elasticsearch import Elasticsearch
# Assegura't d'haver instal·lat la versió correcta! ("pip install 'elasticsearch<9.0.0'")
from elasticsearch.exceptions import ConnectionError as ESConnectionError
import sys
import os

# Afegir el directori 'ia' al path per importar els mòduls
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ia'))
try:
    from ai_service import AIService
    AI_ENABLED = True
except ImportError as e:
    print(f"⚠️ No s'ha pogut carregar el servei d'IA: {e}")
    AI_ENABLED = False

# Creem una instància de l'aplicació
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],     # Permitir todo
    allow_credentials=False, # <--- IMPORTANTE: Poner esto en False si usas "*"
    allow_methods=["*"],
    allow_headers=["*"],
)
# Inicialitzar servei d'IA
ai_service = None
if AI_ENABLED:
    try:
        ai_service = AIService()
        print("✓ Servei d'IA inicialitzat correctament")
    except Exception as e:
        print(f"✗ Error inicialitzant servei d'IA: {e}")
        AI_ENABLED = False

# --- Diccionari de Mapeig per a les Estadístiques ---
# Tradueix els noms amigables (URL) als noms dels camps a Elasticsearch
STAT_MAPPING = {
    "velocitat": "speed",
    "hp": "hp",
    "atac": "attack",
    "defensa": "defense",
    "atac_especial": "special_attack",
    "defensa_especial": "special_defense"
}


# --- Dependència d'Elasticsearch ---
def get_es_client():
    try:
        es = Elasticsearch(
            hosts=["http://127.0.0.1:9200"],
            verify_certs=False
        )
        if not es.ping():
            raise ESConnectionError("Ping a Elasticsearch ha fallat.")
        yield es
    except ESConnectionError:
        raise HTTPException(status_code=503, detail="El servei d'Elasticsearch no està disponible.")
    finally:
        pass

# --- Endpoints de l'API ---

@app.get("/")
def ruta_arrel():
    return {"missatge": "El servidor FastAPI del PokeBuilder funciona!"}

# --- ENDPOINT UNIFICAT: Cerca, Ordenació i Filtre per Tipus ---
@app.get("/api/v1/pokemon/search")
def search_pokemon(
        q: str = None,          # Opcional: text per buscar (nom o ID)
        stat: str = None,       # Opcional: estadística, 'id' o 'nom' per ordenar
        order: str = "desc",    # Opcional: direcció (asc/desc)
        types: List[str] = Query(None), # Opcional: Llista de tipus

        # --- Filtres d'Estadístiques (Min/Max) ---
        hp_min: int = None, hp_max: int = None,
        attack_min: int = None, attack_max: int = None,
        defense_min: int = None, defense_max: int = None,
        special_attack_min: int = None, special_attack_max: int = None,
        special_defense_min: int = None, special_defense_max: int = None,
        speed_min: int = None, speed_max: int = None,

        # --- Filtre de Banejats ---
        exclude_banned: bool = Query(False), # Si és True, amaga els banejats

        es_client: Elasticsearch = Depends(get_es_client)
):
    """
    Endpoint Unificat:
    - Cerca per nom o ID (autocompletar).
    - Filtre per tipus (paràmetre 'types').
    - Filtre per rang d'estadístiques (hp_min, speed_max, etc.).
    - Filtre per banejats (exclude_banned=True).
    - Ordenació per stats, id o nom (paràmetre 'stat').
    """

    # Construïm una consulta "bool" que permet combinar condicions
    must_clauses = []
    filter_clauses = []

    # 1. Cerca per text o ID (q) -> Va al 'must'
    if q:
        should_conditions = []

        # A. Cerca per prefix del nom (Sempre)
        should_conditions.append({
            "prefix": {
                "name.keyword": {
                    "value": q.lower()
                }
            }
        })

        # B. Cerca per ID (Autocompletar numèric)
        if q.isdigit():
            # Fem servir un script per convertir l'ID a string i comprovar si comença pel número
            should_conditions.append({
                "script": {
                    "script": {
                        "source": "doc['pokedex_id'].value.toString().startsWith(params.prefix)",
                        "params": {"prefix": q}
                    }
                }
            })

        # Afegim la condició: Ha de complir A o B
        must_clauses.append({
            "bool": {
                "should": should_conditions,
                "minimum_should_match": 1
            }
        })
    else:
        # Si no hi ha text, ni filtres de tipus, ni filtres d'stats, ni filtre de banejats, volem tots.
        # Però si hi ha filtres, el 'match_all' és implícit.
        has_stats_filters = any([
            hp_min, hp_max, attack_min, attack_max, defense_min, defense_max,
            special_attack_min, special_attack_max, special_defense_min, special_defense_max,
            speed_min, speed_max
        ])

        if not types and not has_stats_filters and not exclude_banned:
            must_clauses.append({"match_all": {}})

    # 2. Filtre per Tipus (si n'hi ha) -> Va al 'filter'
    if types:
        types_lower = [t.lower() for t in types]
        filter_clauses.append({
            "terms": {
                "types": types_lower
            }
        })

    # 3. Filtre per Banejats (NOU) -> Va al 'filter'
    if exclude_banned:
        filter_clauses.append({
            "term": {
                "is_banned": False  # Només volem els que NO estan banejats
            }
        })

    # 4. Filtres per Rang d'Estadístiques -> Va al 'filter'
    # Creem una llista amb la configuració de cada filtre
    stats_configs = [
        ("stats.hp", hp_min, hp_max),
        ("stats.attack", attack_min, attack_max),
        ("stats.defense", defense_min, defense_max),
        ("stats.special_attack", special_attack_min, special_attack_max),
        ("stats.special_defense", special_defense_min, special_defense_max),
        ("stats.speed", speed_min, speed_max)
    ]

    for field, min_val, max_val in stats_configs:
        if min_val is not None or max_val is not None:
            range_query = {}
            if min_val is not None:
                range_query["gte"] = min_val # Greater than or equal (Major o igual)
            if max_val is not None:
                range_query["lte"] = max_val # Less than or equal (Menor o igual)

            filter_clauses.append({
                "range": {
                    field: range_query
                }
            })

    # 5. Construir l'ordenació (Sort)
    sort_criteria = []

    if stat:
        stat_lower = stat.lower()
        elastic_stat_field = None

        # Comprovem si vol ordenar per ID o Nom
        if stat_lower in ["id", "pokedex_id", "numero"]:
            elastic_stat_field = "pokedex_id"
        elif stat_lower in ["nom", "name", "nombre"]:
            elastic_stat_field = "name.keyword"
        else:
            # Si no és ID ni Nom, mirem si és una estadística de combat
            stat_key = STAT_MAPPING.get(stat_lower)
            if stat_key:
                elastic_stat_field = f"stats.{stat_key}"

        # Si després de tot això no tenim camp, l'stat no és vàlid
        if not elastic_stat_field:
            raise HTTPException(
                status_code=400,
                detail=f"Paràmetre 'stat' invàlid. Prova amb: id, nom, {', '.join(STAT_MAPPING.keys())}"
            )

        # Validar l'ordre
        if order.lower() not in ["asc", "desc"]:
            raise HTTPException(status_code=400, detail="L'ordre ha de ser 'asc' o 'desc'")

        # Afegim el criteri d'ordenació
        sort_criteria.append({ elastic_stat_field: {"order": order.lower()} })
    else:
        # PER DEFECTE: Ordenem per ID (ascendent)
        sort_criteria.append({ "pokedex_id": {"order": "asc"} })

    # 6. Muntar la consulta final completa
    query = {
        "query": {
            "bool": {
                "must": must_clauses,
                "filter": filter_clauses
            }
        },
        "sort": sort_criteria,
        "size": 200
    }

    # 7. Executar i Retornar
    response = es_client.search(index="pokemon", body=query)
    results = []
    for hit in response['hits']['hits']:
        pokemon = hit['_source']
        results.append({
            "pokedex_id": pokemon.get("pokedex_id"),
            "name": pokemon.get("name", "N/A").capitalize(),
            "types": pokemon.get("types"),
            "sprite_url": f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pokemon.get('pokedex_id')}.png",
            "stats": pokemon.get("stats"),
            "is_banned": pokemon.get("is_banned", False) # Retornem l'estat per si el frontend vol posar una icona 🚫
        })
    return results

# Endpoint: Cercador d'Habilitats
@app.get("/api/v1/pokemon/{pokedex_id}/abilities")
def get_pokemon_abilities(
        pokedex_id: int,
        q: Optional[str] = None,
        es_client: Elasticsearch = Depends(get_es_client)
):
    """
    Retorna la llista d'habilitats (abilities) d'un Pokémon específic.
    Si s'envia 'q', filtra les habilitats que continguin aquest text al nom.
    """

    # 1. Primer busquem el Pokémon a Elasticsearch pel seu ID
    query = {
        "query": {
            "term": {
                "pokedex_id": pokedex_id
            }
        }
    }

    response = es_client.search(index="pokemon", body=query)

    # Si no trobem el Pokémon, retornem error 404
    if response['hits']['total']['value'] == 0:
        raise HTTPException(status_code=404, detail="Pokémon no trobat")

    # 2. Extraiem la llista completa d'habilitats del document
    pokemon_data = response['hits']['hits'][0]['_source']
    abilities_list = pokemon_data.get("abilities", [])

    # 3. Si hi ha un terme de cerca 'q', filtrem la llista amb Python
    if q:
        q = q.lower()
        # Filtrem: Guardem l'habilitat si el terme de cerca està DINS del nom
        filtered_abilities = [
            ability for ability in abilities_list
            if q in ability['name'].lower()
        ]
        return filtered_abilities

    # Si no hi ha cerca, retornem totes les habilitats
    return abilities_list

# Endpoint: Cercador de Moviments
@app.get("/api/v1/pokemon/{pokedex_id}/moves")
def get_pokemon_moves(
        pokedex_id: int,
        q: Optional[str] = None,
        es_client: Elasticsearch = Depends(get_es_client)
):
    """
    Retorna la llista de moviments (moves_pool) d'un Pokémon específic.
    Si s'envia 'q', filtra els moviments que continguin aquest text al nom.
    """

    # 1. Primer busquem el Pokémon a Elasticsearch pel seu ID
    query = {
        "query": {
            "term": {
                "pokedex_id": pokedex_id
            }
        }
    }

    response = es_client.search(index="pokemon", body=query)

    # Si no trobem el Pokémon, retornem error 404
    if response['hits']['total']['value'] == 0:
        raise HTTPException(status_code=404, detail="Pokémon no trobat")

    # 2. Extraiem la llista completa de moviments del document
    pokemon_data = response['hits']['hits'][0]['_source']
    moves_pool = pokemon_data.get("moves_pool", [])

    # 3. Si hi ha un terme de cerca 'q', filtrem la llista amb Python
    if q:
        q = q.lower()
        # Filtrem: Guardem el moviment si el terme de cerca està DINS del nom del moviment
        filtered_moves = [
            move for move in moves_pool
            if q in move['name'].lower()
        ]
        return filtered_moves

    # Si no hi ha cerca, retornem tots els moviments
    return moves_pool

# Endpoint: Cercador d'Objectes (Items) ---
@app.get("/api/v1/items/search")
def search_items_by_name(q: str, es_client: Elasticsearch = Depends(get_es_client)):
    """
    Busca objectes (items) pel seu nom a l'índex 'items'.
    """
    # Consulta prefix al camp 'name' de l'índex 'items'
    # Nota: Si tens 'name.keyword' a items, fes servir aquest. Si no, 'name' sol funcionar.
    query = {
        "query": {
            "prefix": {
                "name": {
                    "value": q.lower()
                }
            }
        }
    }

    response = es_client.search(index="items", body=query)

    results = []
    for hit in response['hits']['hits']:
        item = hit['_source']
        results.append({
            "item_id": item.get("item_id"),
            "name": item.get("name", "N/A"),
            "category": item.get("category"),
            "cost": item.get("cost"),
            "effect": item.get("effect"),
            # Generem la URL de la imatge fent servir el nom de l'objecte (estàndard PokeAPI)
            "sprite_url": f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/items/{item.get('name')}.png"
        })

    return results

# Endpoint: Equips d'un Usuari ---
@app.get("/api/v1/teams/user/{user_id}")
def get_user_teams(user_id: str, es_client: Elasticsearch = Depends(get_es_client)):
    """
    Retorna tots els equips creats per un usuari específic (filtrant per user_id).
    """
    query = {
        "query": {
            "term": {
                "user_id": user_id # user_id és keyword, cerca exacta
            }
        }
    }

    try:
        response = es_client.search(index="teams", body=query)
    except Exception:
        # Si l'índex no existeix o falla, retornem llista buida
        return []

    results = []
    for hit in response['hits']['hits']:
        team = hit['_source']
        # És molt útil retornar també l'ID del document d'Elastic per poder editar/esborrar l'equip després
        team['id'] = hit['_id']
        results.append(team)

    return results

# Endpoint: Obtenir detalls d'un Pokémon
@app.get("/api/v1/pokemon/{pokedex_id}")
def get_pokemon_details(pokedex_id: int, es_client: Elasticsearch = Depends(get_es_client)):
    """
    Retorna tota la informació d'un Pokémon a partir del seu número de Pokédex.
    """
    query = {
        "query": {
            "term": {
                "pokedex_id": pokedex_id
            }
        }
    }
    response = es_client.search(index="pokemon", body=query)
    if response['hits']['total']['value'] > 0:
        return response['hits']['hits'][0]['_source']
    else:
        raise HTTPException(status_code=404, detail="Pokémon no trobat")

# --- ENDPOINTS D'IA ---

class TeamRequest(BaseModel):
    """Model per a les peticions d'equip."""
    team_ids: List[int]

@app.post("/api/v1/ai/recommend")
def recommend_pokemon(request: TeamRequest):
    """
    Retorna recomanacions de Pokémon basades en l'equip actual.
    
    Args:
        request: Objecte amb la llista d'IDs de l'equip actual
        
    Returns:
        Llista de recomanacions amb puntuacions i raonament
    """
    if not AI_ENABLED or ai_service is None:
        raise HTTPException(
            status_code=503,
            detail="El servei d'IA no està disponible"
        )
    
    try:
        team_ids = request.team_ids
        
        # Validar que no hi hagi més de 5 Pokémon
        if len(team_ids) >= 6:
            raise HTTPException(
                status_code=400,
                detail="L'equip ja està complet (6 Pokémon)"
            )
        
        # Generar recomanacions
        recommendations = ai_service.recommend_pokemon(team_ids, top_n=5)
        
        return {
            "success": True,
            "team_size": len(team_ids),
            "recommendations": recommendations
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generant recomanacions: {str(e)}"
        )

@app.post("/api/v1/ai/analyze")
def analyze_team(request: TeamRequest):
    """
    Analitza un equip i retorna les seves fortaleses i debilitats.
    
    Args:
        request: Objecte amb la llista d'IDs de l'equip
        
    Returns:
        Anàlisi detallat de l'equip
    """
    if not AI_ENABLED or ai_service is None:
        raise HTTPException(
            status_code=503,
            detail="El servei d'IA no està disponible"
        )
    
    try:
        analysis = ai_service.analyze_team(request.team_ids)
        
        return {
            "success": True,
            "analysis": analysis
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error analitzant equip: {str(e)}"
        )

@app.get("/api/v1/ai/status")
def ai_status():
    """
    Retorna l'estat del servei d'IA.
    """
    return {
        "enabled": AI_ENABLED,
        "service_initialized": ai_service is not None,
        "types_loaded": len(ai_service.type_chart) if ai_service else 0
    }



# --- BLOQUE DE ARRANQUE ---
if __name__ == "__main__":
    import uvicorn
    # Esto permite ejecutar el script directamente con el botón "Run" de IntelliJ
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)