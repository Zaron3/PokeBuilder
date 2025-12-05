from idlelib.query import Query

from fastapi import FastAPI, HTTPException, Depends
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

# Configurar CORS per permetre peticions des del frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producció, especificar els orígens permesos
    allow_credentials=True,
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

# --- ENDPOINT UNIFICAT: Cerca i Ordenació ---
@app.get("/api/v1/pokemon/search")
def search_pokemon(
        q: str = None,          # Opcional: text per buscar (nom)
        stat: str = None,       # Opcional: estadística per ordenar
        order: str = "desc",    # Opcional: direcció (asc/desc)
        types: List[str] = Query(None), # Opcional: Llista de tipus (ex: ?types=fire&types=water)
        es_client: Elasticsearch = Depends(get_es_client)
):
    """
    Endpoint Unificat: Permet buscar per nom, filtrar per tipus i ordenar per estadística.

    Exemple d'ús:
    - /api/v1/pokemon/search?types=fire&types=flying (Torna Charizard, etc.)
    - /api/v1/pokemon/search?q=pika&types=electric (Torna Pikachu)
    """

    # Construïm una consulta "bool" que permet combinar condicions
    must_clauses = []
    filter_clauses = []

    # 1. Cerca per text (si n'hi ha) -> Va al 'must'
    if q:
        must_clauses.append({
            "prefix": {
                "name.keyword": {
                    "value": q.lower()
                }
            }
        })
    else:
        # Si no hi ha text ni filtres, volem tots els resultats.
        # Però si hi ha filtres, el 'match_all' és implícit.
        if not types:
            must_clauses.append({"match_all": {}})

    # 2. Filtre per Tipus (si n'hi ha) -> Va al 'filter'
    if types:
        # Normalitzem a minúscules per si de cas
        types_lower = [t.lower() for t in types]
        # La consulta 'terms' funciona com un OR:
        # Busca documents on el camp 'types' contingui ALMENYS UN dels valors de la llista.
        filter_clauses.append({
            "terms": {
                "types": types_lower
            }
        })

    # 3. Construir l'ordenació (Sort)
    sort_criteria = []

    if stat:
        # Si s'ha demanat una estadística concreta, validem i ordenem per ella
        stat_key = STAT_MAPPING.get(stat.lower())
        if not stat_key:
            raise HTTPException(
                status_code=400,
                detail=f"Paràmetre 'stat' invàlid. Prova amb un de: {', '.join(STAT_MAPPING.keys())}"
            )

        # Validar l'ordre
        if order.lower() not in ["asc", "desc"]:
            raise HTTPException(status_code=400, detail="L'ordre ha de ser 'asc' o 'desc'")

        # Afegim el criteri d'ordenació per estadística
        elastic_stat_field = f"stats.{stat_key}"
        sort_criteria.append({ elastic_stat_field: {"order": order.lower()} })
    else:
        # PER DEFECTE: Ordenem per ID (ascendent)
        sort_criteria.append({ "pokedex_id": {"order": "asc"} })

    # 4. Muntar la consulta final completa
    query = {
        "query": {
            "bool": {
                "must": must_clauses,
                "filter": filter_clauses
            }
        },
        "sort": sort_criteria,
        "size": 200 # Limitem a 200 resultats per pàgina
    }

    # 5. Executar i Retornar
    response = es_client.search(index="pokemon", body=query)
    results = []
    for hit in response['hits']['hits']:
        pokemon = hit['_source']
        results.append({
            "pokedex_id": pokemon.get("pokedex_id"),
            "name": pokemon.get("name", "N/A").capitalize(),
            "types": pokemon.get("types"),
            "sprite_url": f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pokemon.get('pokedex_id')}.png",
            "stats": pokemon.get("stats")
        })
    return results

# Endpoint: Cercador d'Habilitats
# **** AQUEST TAMBÉ HA D'ANAR ABANS DE .../{pokedex_id} ****
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
# **** AQUEST TAMBÉ HA D'ANAR ABANS DE .../{pokedex_id} ****
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

# --- NOU ENDPOINT: Cercador d'Objectes (Items) ---
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

# Endpoint 3.2: Obtenir detalls d'un Pokémon
# **** AQUEST HA D'ANAR DESPRÉS DE .../sort ****
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