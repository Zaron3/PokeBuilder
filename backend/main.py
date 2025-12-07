

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict
from elasticsearch import Elasticsearch
# Assegura't d'haver instal·lat la versió correcta! ("pip install 'elasticsearch<9.0.0'")
from elasticsearch.exceptions import ConnectionError as ESConnectionError
import sys
import os
import time
from datetime import datetime, timedelta

# --- IMPORTS DE SEGURETAT ---
from passlib.context import CryptContext
from jose import JWTError, jwt
from starlette import status

# Afegir el directori 'ia' al path per importar els mòduls
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'ia'))
try:
    from ai_service import AIService
    AI_ENABLED = True
except ImportError as e:
    print(f"⚠️ No s'ha pogut carregar el servei d'IA: {e}")
    AI_ENABLED = False

# --- CONFIGURACIÓ DE SEGURETAT ---
SECRET_KEY = "clau_super_secreta_del_pokebuilder_canviar_en_produccio"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 # 24 hores

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

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


# --- MODELS DE PYDANTIC (Inputs) ---

class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    favorite_pokemon: Optional[str] = "Pikachu"

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: str

    # Model per als membres de l'equip (Pokémon individuals)
class TeamMember(BaseModel):
    base_pokemon: str
    nickname: Optional[str] = None
    item: Optional[str] = None
    ability: Optional[str] = None
    tera_type: Optional[str] = None
    nature: Optional[str] = None
    moves: List[str] = []
    evs: Dict[str, int] = {} # Ex: {"hp": 252, "attack": 252}

# Model per crear un equip nou
class TeamCreate(BaseModel):
    team_id: Optional[str] = None
    team_name: str
    description: Optional[str] = None
    format: str
    team_members: List[TeamMember]



# --- Diccionari de Mapeig per a les Estadístiques ---
STAT_MAPPING = {
    # Noms en Català (Mantenim els que tenies)
    "velocitat": "speed",
    "hp": "hp",
    "atac": "attack",
    "defensa": "defense",
    "atac_especial": "special_attack",
    "defensa_especial": "special_defense",

    # --- AFEGEIX AQUESTS (Anglès) ---
    # Això permet que el frontend envii 'speed' i el backend sàpiga que és 'stats.speed'
    "speed": "speed",
    "attack": "attack",
    "defense": "defense",
    "special_attack": "special_attack",
    "special_defense": "special_defense"
}

# --- FUNCIONS AUXILIARS DE SEGURETAT ---

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

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

# --- Dependència per obtenir l'usuari actual (Protecció de rutes) ---
async def get_current_user(token: str = Depends(oauth2_scheme), es: Elasticsearch = Depends(get_es_client)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No s'han pogut validar les credencials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Busquem l'usuari a Elastic
    query = {"query": {"match": {"username": username}}}
    response = es.search(index="users", body=query)

    if response['hits']['total']['value'] == 0:
        raise credentials_exception

    user = response['hits']['hits'][0]['_source']
    return user

# --- ENDPOINTS D'AUTENTICACIÓ ---

@app.post("/api/v1/auth/register", status_code=201)
def register_user(user_data: UserRegister, es: Elasticsearch = Depends(get_es_client)):
    """
    Registra un nou usuari a la base de dades.
    """
    # 1. Comprovar si l'usuari o l'email ja existeixen
    query_check = {
        "query": {
            "bool": {
                "should": [
                    {"term": {"username": user_data.username}},
                    {"term": {"email": user_data.email}}
                ]
            }
        }
    }

    # Comprovem si l'índex existeix abans de cercar
    if es.indices.exists(index="users"):
        response = es.search(index="users", body=query_check)
        if response['hits']['total']['value'] > 0:
            raise HTTPException(
                status_code=400,
                detail="L'usuari o el correu electrònic ja estan registrats."
            )

    # 2. Crear l'objecte usuari segons l'estructura definida
    # Generem un ID basat en el temps (timestamp) per tenir un INT únic
    new_user_id = int(time.time())

    hashed_password = get_password_hash(user_data.password)

    new_user_doc = {
        "user_id": new_user_id,
        "username": user_data.username,
        "email": user_data.email,
        "password_hash": hashed_password,
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "is_active": True,
        "profile": {
            "full_name": user_data.full_name,
            "avatar_url": f"https://ui-avatars.com/api/?name={user_data.username}",
            "bio": "Nou entrenador Pokémon!",
            "favorite_pokemon": user_data.favorite_pokemon
        },
        "preferences": {
            "default_format": "vgc",
            "language": "es",
            "theme": "dark"
        }
    }

    # 3. Guardar a Elasticsearch
    # Fem servir l'username com a _id del document per evitar duplicats a nivell intern
    es.index(index="users", id=str(new_user_id), document=new_user_doc)
    es.indices.refresh(index="users") # Forçar refresc perquè estigui disponible de seguida

    return {"message": "Usuari registrat correctament", "user_id": new_user_id, "username": user_data.username}

@app.post("/api/v1/auth/login", response_model=Token)
def login_for_access_token(
        # Fem servir OAuth2PasswordRequestForm en lloc de UserLogin
        form_data: OAuth2PasswordRequestForm = Depends(),
        es: Elasticsearch = Depends(get_es_client)
):
    """
    Inicia sessió. Compatible amb el botó 'Authorize' del Swagger.
    """
    # 1. Buscar l'usuari
    # Nota: OAuth2PasswordRequestForm guarda l'usuari a .username (no importa si és email o nick)
    query = {"query": {"match": {"username": form_data.username}}}

    try:
        response = es.search(index="users", body=query)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuari o contrasenya incorrectes",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if response['hits']['total']['value'] == 0:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuari o contrasenya incorrectes",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = response['hits']['hits'][0]['_source']

    # 2. Verificar contrasenya
    stored_hash = user.get('password_hash')
    is_password_correct = False

    if stored_hash:
        try:
            is_password_correct = verify_password(form_data.password, stored_hash)
        except Exception:
            is_password_correct = False

    if not is_password_correct:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuari o contrasenya incorrectes",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Generar Token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user['username'], "id": user['user_id']},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user['user_id'],
        "username": user['username']
    }

@app.get("/api/v1/users/me")
def read_users_me(current_user: dict = Depends(get_current_user)):
    """
    Retorna la informació de l'usuari actualment autenticat (basat en el token).
    """
    # Eliminem el hash de la contrasenya abans d'enviar-lo per seguretat
    if 'password_hash' in current_user:
        del current_user['password_hash']
    return current_user


# --- Endpoints de l'API ---

@app.get("/")
def ruta_arrel():
    return {"missatge": "El servidor FastAPI del PokeBuilder funciona!"}

# Endpoint: Guardar Equip ---
@app.post("/api/v1/teams", status_code=201)
def create_team(
        team_data: TeamCreate,
        current_user: dict = Depends(get_current_user), # <--- Aquesta línia protegeix l'endpoint
        es: Elasticsearch = Depends(get_es_client)
):
    """
    Desa un nou equip a la base de dades.
    Requereix estar autenticat. El 'user_id' s'agafa automàticament del token.
    """
    try:
        # Convertim el model a diccionari
        team_doc = team_data.dict()

        # Extraiem l'ID si existeix i el traiem del document per no duplicar info
        target_id = team_doc.pop("team_id", None)

        # Injectem l'usuari (Seguretat: sempre el del token)
        team_doc["user_id"] = current_user["username"]

        # --- BLOC DE DATES CORREGIT ---
        now_iso = datetime.now().isoformat()
        team_doc["updated_at"] = now_iso # Sempre actualitzem la data de modificació

        if target_id:
            # CAS ACTUALITZAR: Recuperem la data original per no perdre-la
            try:
                old_doc = es.get(index="teams", id=target_id)
                # Si existeix, copiem la data de creació antiga al nou document
                team_doc["created_at"] = old_doc['_source'].get('created_at', now_iso)
            except Exception:
                # Si no trobem l'antic (rar), posem la data d'ara
                team_doc["created_at"] = now_iso
        else:
            # CAS NOU: Posem la data d'ara
            team_doc["created_at"] = now_iso
        # ------------------------------

        # GUARDAR A ELASTICSEARCH
        # Si passem 'id', Elasticsearch sobreescriu (Update). Si és None, crea nou.
        response = es.index(index="teams", id=target_id, document=team_doc)

        return {
            "success": True,
            "message": "Equip actualitzat" if target_id else "Equip creat",
            "team_id": response["_id"],
            "team_name": team_doc["team_name"]
        }

    except Exception as e:
        print(f"Error guardant equip: {e}")
        raise HTTPException(status_code=500, detail=f"Error guardant l'equip: {str(e)}")


# Endpoint: Esborrar Equip ---
@app.delete("/api/v1/teams/{team_id}")
def delete_team(
        team_id: str,
        current_user: dict = Depends(get_current_user),
        es: Elasticsearch = Depends(get_es_client)
):
    try:
        # 1. Comprovar que l'equip existeix
        team_res = es.get(index="teams", id=team_id)
        team_data = team_res['_source']

        # 2. Comprovar que l'equip pertany a l'usuari que fa la petició (Seguretat)
        if team_data['user_id'] != current_user['username']:
            raise HTTPException(status_code=403, detail="No tens permís per esborrar aquest equip.")

        # 3. Esborrar
        es.delete(index="teams", id=team_id)
        es.indices.refresh(index="teams") # Refresc immediat

        return {"success": True, "message": "Equip esborrat correctament"}

    except Exception:
        raise HTTPException(status_code=404, detail="Equip no trobat o error esborrant.")


    # --- ENDPOINT D'ANÀLISI DE VULNERABILITAT (IA) ---
@app.get("/api/v1/teams/vulnerability")
def get_team_vulnerability(
        team_ids: List[int] = Query(..., description="Llista d'IDs de Pokédex dels 6 Pokémon de l'equip."),
        current_user: dict = Depends(get_current_user) # Protecció de la ruta
):
    """
    Analitza un equip de 6 Pokémon i retorna el tipus elemental al qual l'equip
    és més vulnerable, o si està equilibrat.
    """
    if not AI_ENABLED or ai_service is None:
        raise HTTPException(status_code=503, detail="El servei d'Intel·ligència Artificial no està disponible.")

    if len(team_ids) != 6:
        raise HTTPException(status_code=400, detail="L'equip ha de tenir exactament 6 Pokémon.")

    try:
        analysis = ai_service.get_team_vulnerability(team_ids)
        return analysis

    except Exception as e:
        print(f"Error analitzant vulnerabilitat de l'equip: {e}")
        raise HTTPException(status_code=500, detail=f"Error intern del servidor: {str(e)}")

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

        # AFEGEIX AIXÒ AL FINAL DELS PARÀMETRES:
        limit: int = Query(50, le=1000), # Per defecte 50, màxim 1000
        offset: int = Query(0, ge=0), # <--- AFEGEIX AQUEST PARÀMETRE NOU

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
    # 6. Muntar la consulta final
    query = {
        "query": { "bool": { "must": must_clauses, "filter": filter_clauses } },
        "sort": sort_criteria,
        "size": limit,
        "from": offset  # <--- AFEGEIX AIXÒ AQUÍ (Elasticsearch fa servir "from")
    }

    # 7. Executar i Retornar
    response = es_client.search(index="pokemon", body=query)

    # AFEGEIX AIXÒ: Obtenir el número total real de coincidències
    total_hits = response['hits']['total']['value']

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
    # CANVIA EL RETURN PER AQUEST OBJECTE:
    return {
        "total": total_hits,
        "results": results
    }

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