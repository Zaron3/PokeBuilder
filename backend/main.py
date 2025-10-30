from fastapi import FastAPI, HTTPException, Depends
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError as ESConnectionError, NotFoundError
from fastapi.middleware.cors import CORSMiddleware

# Creem una instància de l'aplicació
app = FastAPI()

# Permet connexions des del frontend (ex: Live Server)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Pots posar el port específic del Live Server, ex: ["http://127.0.0.1:5500"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Dependència d'Elasticsearch ---
# Aquesta funció s'executarà CADA COP que un endpoint la demani.
# És la manera correcta de gestionar connexions a bases de dades a FastAPI.
def get_es_client():
    try:
        # Creem el client
        es = Elasticsearch(
            hosts=["http://localhost:9200"],
            # Pots afegir autenticació aquí si la tinguessis
            # http_auth=('usuari', 'contrasenya')
        )
        # Comprovem que la connexió funciona
        if not es.ping():
            raise ESConnectionError("Ping a Elasticsearch ha fallat.")

        # 'yield' és com un 'return' per a les dependències.
        # Entrega el client 'es' a l'endpoint.
        yield es

    except ESConnectionError:
        # Si hi ha qualsevol error de connexió, enviem un error 503
        # (Servei No Disponible) al frontend.
        raise HTTPException(status_code=503, detail="El servei d'Elasticsearch no està disponible.")
    finally:
        # Aquesta part es podria fer servir per tancar connexions,
        # però el client d'Elasticsearch gestiona això automàticament.
        pass

# --- Endpoints de l'API ---

@app.get("/")
def ruta_arrel():
    return {"missatge": "API del PokeBuilder funcionant! (Connectada a Elastic)"}

# Endpoint 3.1: Cerca de Pokémon per autocompletar
@app.get("/api/v1/pokemon/search")
def search_pokemon_by_name(q: str, es_client: Elasticsearch = Depends(get_es_client)):
    """
    Busca Pokémon pel terme de cerca 'q' i retorna una llista simplificada.
    'es_client' s'injecta automàticament gràcies a Depends(get_es_client).
    """

    # La consulta busca documents que comencin amb el terme de cerca (prefix)
    # Busquem al camp 'name.keyword' per a cerques exactes de prefix.
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

    # Formategem la resposta tal com demana el contracte
    results = []
    for hit in response['hits']['hits']:
        pokemon = hit['_source']
        results.append({
            "pokedex_id": pokemon.get("pokedex_id"),
            "name": pokemon.get("name", "N/A").capitalize(),
            "types": pokemon.get("types"),
            "sprite_url": f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{pokemon.get('pokedex_id')}.png"
        })

    return results

# Endpoint 3.2: Obtenir detalls d'un Pokémon
@app.get("/api/v1/pokemon/{pokedex_id}")
def get_pokemon_details(pokedex_id: int, es_client: Elasticsearch = Depends(get_es_client)):
    """
    Retorna tota la informació d'un Pokémon a partir del seu número de Pokédex.
    """

    # Creem la consulta per buscar un document amb un 'pokedex_id' específic
    query = {
        "query": {
            "term": {
                "pokedex_id": pokedex_id
            }
        }
    }

    response = es_client.search(index="pokemon", body=query)

    if response['hits']['total']['value'] > 0:
        # Retornem el document sencer (el '_source')
        return response['hits']['hits'][0]['_source']
    else:
        # Si no es troba, llancem un error HTTP 404
        raise HTTPException(status_code=404, detail="Pokémon no trobat")

