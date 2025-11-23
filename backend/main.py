from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
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

# Endpoint 3.1: Cerca de Pokémon per autocompletar
@app.get("/api/v1/pokemon/search")
def search_pokemon_by_name(q: str, es_client: Elasticsearch = Depends(get_es_client)):
    """
    Busca Pokémon pel terme de cerca 'q' i retorna una llista simplificada.
    """
    query = {
        "query": {
            "prefix": {
                "name.keyword": {
                    "value": q.lower()
                }
            }
        }
    }
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

# --- NOU ENDPOINT: Ordenar Pokémon per Estadística ---
# **** AQUEST HA D'ANAR ABANS DE .../{pokedex_id} ****
@app.get("/api/v1/pokemon/sort")
def sort_pokemon_by_stat(
        stat: str,
        order: str = "desc",
        es_client: Elasticsearch = Depends(get_es_client)
):
    """
    Retorna tots els Pokémon ordenats per una estadística específica.
    """

    # --- Validació de Paràmetres ---
    stat_key = STAT_MAPPING.get(stat.lower())
    if not stat_key:
        raise HTTPException(
            status_code=400,
            detail=f"Paràmetre 'stat' invàlid. Prova amb un de: {', '.join(STAT_MAPPING.keys())}"
        )

    order_direction = order.lower()
    if order_direction not in ["asc", "desc"]:
        raise HTTPException(
            status_code=400,
            detail="Paràmetre 'order' invàlid. Ha de ser 'asc' o 'desc'."
        )

    elastic_stat_field = f"stats.{stat_key}"

    # --- Construcció de la Consulta ---
    query = {
        "query": {
            "match_all": {}
        },
        "sort": [
            {
                elastic_stat_field: {
                    "order": order_direction
                }
            }
        ],
        "size": 200
    }

    # --- Execució i Resposta ---
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