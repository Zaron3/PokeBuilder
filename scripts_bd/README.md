# Scripts de Base de Dades - PokeBuilder

Aquest directori conté els scripts necessaris per configurar i poblar la base de dades Elasticsearch del projecte PokeBuilder.

## Estructura de Fitxers

### Configuració d'Índexs
- **`crear-indexs.json`**: Script per crear tots els índexs d'Elasticsearch (pokemon, moves, teams, types, items, abilities, natures, users)

### Scripts d'Ingesta
- **`ingesta_completa.py`**: ⭐ **Script intel·ligent** que executa només els scripts necessaris (verifica quins índexs tenen dades)
- **`ingesta_pokemon.py`**: Importa dades de Pokémon des de PokéAPI a Elasticsearch (inclou abilities, moves_pool i is_banned)
- **`ingesta_tipus.py`**: Importa tots els tipus de Pokémon amb les seves relacions d'efectivitat des de PokéAPI
- **`ingesta_moves.py`**: Importa tots els moviments de Pokémon des de PokéAPI a Elasticsearch
- **`ingesta_items.py`**: Importa tots els items/objectes de Pokémon des de PokéAPI a Elasticsearch
- **`ingesta_abilities.py`**: Importa totes les habilitats de Pokémon des de PokéAPI a Elasticsearch
- **`ingesta_natures.py`**: Importa totes les naturalezas de Pokémon des de PokéAPI a Elasticsearch
- **`ingesta_usuarios.py`**: Crea els usuaris predefinits a la base de dades (jordi_bolance, jordi_barnola, pol_torrent, jordi_roura, marc_cassanmagnago)
- **`ingesta_teams.py`**: Crea equips predefinits per als usuaris 1 i 2 (2 equips per usuari)
- **`marcar_pokemon_prohibits.py`**: Marca els Pokémon prohibits en competitivo (llegendaris, míticos, etc.)

### Dades de Prova
- **`llista-pokemon-prova.json`**: Exemples de Pokémon per a proves
- **`llista-tipus-prova.json`**: Exemples de tipus amb relacions d'efectivitat per a proves
- **`crear-equip-prova.json`**: Exemple d'equip complet per a proves
- **`crear-usuari-prova.json`**: Exemples de com crear usuaris via Kibana Dev Tools

## Ús

### 0. Ingesta Automàtica Intel·ligent (Recomanat)

Executa el script intel·ligent que només importa el que cal:

```bash
python ingesta_completa.py
```

Aquest script:
- ✅ Verifica quins índexs tenen dades suficients
- ✅ Només executa els scripts d'ingesta necessaris
- ✅ Evita reimportar dades que ja existeixen
- ✅ Crea automàticament usuaris si no n'hi ha cap
- ✅ Crea automàticament equips si no n'hi ha cap
- ✅ Mostra un resum final de l'estat de tots els índexs

**Exemple d'ús:**
- Si ja tens Pokémon, tipus i moviments → només importarà items, abilities i natures si falten
- Si tot està complet → no executarà res

### 1. Crear els Índexs

Primer, crea tots els índexs necessaris executant les comandes del fitxer `crear-indexs.json` a Kibana Dev Tools o utilitzant l'API REST d'Elasticsearch.

**Amb curl:**
```bash
curl -X PUT "localhost:9200/pokemon" -H 'Content-Type: application/json' -d @crear-indexs.json
```

**Amb Kibana Dev Tools:**
Copia i enganxa les comandes del fitxer `crear-indexs.json` a la consola de Kibana.

### 2. Importar Tipus de Pokémon

Executa el script per importar tots els tipus amb les seves relacions d'efectivitat:

```bash
python ingesta_tipus.py
```

Aquest script:
- Obté tots els tipus disponibles de PokéAPI
- Extrau les relacions d'efectivitat (debilidades, resistencias, inmunidades)
- Insereix les dades a l'índex `types` d'Elasticsearch

### 3. Importar Pokémon

Executa el script per importar Pokémon:

```bash
python ingesta_pokemon.py
```

Per defecte, importa els Pokémon amb IDs del 1 al 1025. Pots modificar el rang a l'script.

Aquest script importa:
- Informació bàsica (pokedex_id, name, types, stats)
- **Abilities** (habilitats amb indicador de si són ocultes)
- **Moves_pool** (pool de moviments disponibles amb mètode d'aprenentatge)

### 4. Importar Moviments

Executa el script per importar tots els moviments:

```bash
python ingesta_moves.py
```

Aquest script:
- Obté tots els moviments disponibles de PokéAPI (més de 900 moviments)
- Extrau informació completa (tipus, categoria, poder, precisió, PP, descripció)
- Insereix les dades a l'índex `moves` d'Elasticsearch

**Nota:** Aquest procés pot trigar uns minuts degut al gran nombre de moviments.

### 5. Importar Items/Objectes

Executa el script per importar tots els items:

```bash
python ingesta_items.py
```

Aquest script:
- Obté tots els items disponibles de PokéAPI (més de 2000 items)
- Extrau informació completa (categoria, cost, descripció, efecte, atributs)
- Insereix les dades a l'índex `items` d'Elasticsearch

**Nota:** Aquest procés pot trigar uns minuts degut al gran nombre d'items.

### 6. Importar Habilitats

Executa el script per importar totes les habilitats:

```bash
python ingesta_abilities.py
```

Aquest script:
- Obté totes les habilitats disponibles de PokéAPI (més de 300 habilitats)
- Extrau informació completa (descripció, efecte, generació)
- Insereix les dades a l'índex `abilities` d'Elasticsearch

**Nota:** Aquest procés és relativament ràpid.

### 7. Importar Naturalezas

Executa el script per importar totes les naturalezas:

```bash
python ingesta_natures.py
```

Aquest script:
- Obté totes les naturalezas disponibles de PokéAPI (25 naturalezas)
- Extrau informació completa (estadística que augmenta, que disminueix, sabors preferits)
- Insereix les dades a l'índex `natures` d'Elasticsearch

**Nota:** Aquest procés és molt ràpid (només 25 naturalezas).

### 8. Marcar Pokémon Prohibits

Executa el script per marcar els Pokémon prohibits en competitivo:

```bash
python marcar_pokemon_prohibits.py
```

Aquest script:
- Marca tots els Pokémon com a NO prohibits per defecte
- Marca com a PROHIBITS els llegendaris, míticos i altres Pokémon restringits
- Inclou una llista predefinida de Pokémon prohibits (pots modificar-la al script)

**Nota:** Pots modificar la llista `pokemon_ids_prohibits` al script segons les regles del format que utilitzis (VGC, Smogon, etc.).

### 9. Crear Usuaris Predefinits

Executa l'script per crear els usuaris predefinits:

```bash
python ingesta_usuarios.py
```

Aquest script crea 5 usuaris predefinits:
- **jordi_bolance** (user_id: 1)
- **jordi_barnola** (user_id: 2)
- **pol_torrent** (user_id: 3)
- **jordi_roura** (user_id: 4)
- **marc_cassanmagnago** (user_id: 5)

Si un usuari ja existeix (per `user_id` o `username`), l'script l'actualitzarà en lloc de crear-lo de nou.

**Nota:** L'script `ingesta_completa.py` executarà automàticament aquest script si detecta que no hi ha cap usuari a la base de dades.

### 10. Crear Equips Predefinits

Executa l'script per crear els equips predefinits:

```bash
python ingesta_teams.py
```

Aquest script crea 4 equips predefinits:
- **2 equips per a l'usuari 1 (jordi_bolance)**:
  - "Equip de Sol VGC" - Equip VGC basat en Sol (6 Pokémon)
  - "Equip Offensiu OU" - Equip ofensiu per a Smogon OU (3 Pokémon)
- **2 equips per a l'usuari 2 (jordi_barnola)**:
  - "Equip Balance VGC" - Equip balancejat per a VGC Reg G (6 Pokémon)
  - "Equip Rain OU" - Equip basat en pluja per a Smogon OU (3 Pokémon)

Si un equip ja existeix (per `team_name` i `user_id`), l'script l'actualitzarà en lloc de crear-lo de nou.

**Nota:** L'script `ingesta_completa.py` executarà automàticament aquest script si detecta que no hi ha cap equip a la base de dades.

### 11. Dades de Prova

Pots utilitzar els fitxers JSON de prova per inserir dades d'exemple directament a Elasticsearch utilitzant l'API REST o Kibana Dev Tools.

## Estructura de l'Índex `types`

L'índex `types` conté la informació de cada tipus de Pokémon:

- **`type_id`**: ID numèric del tipus
- **`name`**: Nom del tipus (ex: "fire", "water", "grass")
- **`double_damage_from`**: Llista de tipus que fan doble dany a aquest tipus (debilidades)
- **`half_damage_from`**: Llista de tipus que fan mig dany a aquest tipus (resistencias)
- **`no_damage_from`**: Llista de tipus que no fan dany a aquest tipus (inmunidades)
- **`double_damage_to`**: Llista de tipus als quals aquest tipus fa doble dany (fortalezas)
- **`half_damage_to`**: Llista de tipus als quals aquest tipus fa mig dany
- **`no_damage_to`**: Llista de tipus als quals aquest tipus no fa dany

## Requisits

- Python 3.x
- Biblioteca `requests` de Python: `pip install requests`
- Elasticsearch funcionant a `localhost:9200`
- Accés a Internet per connectar-se a PokéAPI

## Exemples de Consultes

### Obtenir tots els tipus
```
GET /types/_search
```

### Trobar tipus efectius contra un tipus específic
```
GET /types/_search
{
  "query": {
    "term": {
      "double_damage_to": "water"
    }
  }
}
```

### Trobar debilidades d'un tipus
```
GET /types/_search
{
  "query": {
    "term": {
      "name.keyword": "fire"
    }
  }
}
```

## Estructura de l'Índex `moves`

L'índex `moves` conté la informació de cada moviment de Pokémon:

- **`move_id`**: ID numèric del moviment
- **`name`**: Nom del moviment (ex: "thunderbolt", "flamethrower")
- **`type`**: Tipus del moviment (ex: "electric", "fire")
- **`category`**: Categoria del moviment ("physical", "special", o "status")
- **`power`**: Poder del moviment (0 per a moviments d'estat)
- **`accuracy`**: Precisió del moviment (0-100)
- **`pp`**: Punts de poder (Power Points)
- **`description`**: Descripció del moviment

### Exemples de Consultes per Moviments

### Obtenir tots els moviments
```
GET /moves/_search
```

### Trobar moviments d'un tipus específic
```
GET /moves/_search
{
  "query": {
    "term": {
      "type": "fire"
    }
  }
}
```

### Trobar moviments físics amb poder > 100
```
GET /moves/_search
{
  "query": {
    "bool": {
      "must": [
        { "term": { "category": "physical" } },
        { "range": { "power": { "gt": 100 } } }
      ]
    }
  }
}
```

## Estructura de l'Índex `items`

L'índex `items` conté la informació de cada item/objecte de Pokémon:

- **`item_id`**: ID numèric de l'item
- **`name`**: Nom de l'item (ex: "potion", "master-ball", "leftovers")
- **`category`**: Categoria de l'item (ex: "medicine", "pokeballs", "held-items")
- **`cost`**: Cost de l'item en Pokédòlars
- **`description`**: Descripció de l'item
- **`effect`**: Efecte detallat de l'item
- **`attributes`**: Llista d'atributs (ex: ["holdable", "consumable"])

### Exemples de Consultes per Items

### Obtenir tots els items
```
GET /items/_search
```

### Buscar items d'una categoria específica
```
GET /items/_search
{
  "query": {
    "term": {
      "category": "held-items"
    }
  }
}
```

### Buscar un item per nom
```
GET /items/_search
{
  "query": {
    "match": {
      "name": "master-ball"
    }
  }
}
```

## Estructura de l'Índex `abilities`

L'índex `abilities` conté la informació de cada habilitat de Pokémon:

- **`ability_id`**: ID numèric de l'habilitat
- **`name`**: Nom de l'habilitat (ex: "blaze", "intimidate", "overgrow")
- **`description`**: Descripció de l'habilitat
- **`effect`**: Efecte detallat de l'habilitat
- **`generation`**: Generació on va aparèixer per primera vegada (ex: "generation-i")

### Exemples de Consultes per Habilitats

### Obtenir totes les habilitats
```
GET /abilities/_search
```

### Buscar una habilitat per nom
```
GET /abilities/_search
{
  "query": {
    "match": {
      "name": "blaze"
    }
  }
}
```

### Buscar habilitats d'una generació específica
```
GET /abilities/_search
{
  "query": {
    "term": {
      "generation": "generation-i"
    }
  }
}
```

## Estructura de l'Índex `natures`

L'índex `natures` conté la informació de cada naturalesa de Pokémon:

- **`nature_id`**: ID numèric de la naturalesa
- **`name`**: Nom de la naturalesa (ex: "adamant", "modest", "jolly")
- **`increased_stat`**: Estadística que augmenta en un 10% (ex: "attack", "special-attack", null per a neutral)
- **`decreased_stat`**: Estadística que disminueix en un 10% (ex: "special-attack", "attack", null per a neutral)
- **`likes_flavor`**: Sabor de baya que li agrada (ex: "spicy", "dry", "sweet", "bitter", "sour")
- **`hates_flavor`**: Sabor de baya que odia (ex: "spicy", "dry", "sweet", "bitter", "sour")

**Nota:** Les naturalezas neutrals (com "Hardy", "Docile", etc.) no augmenten ni disminueixen cap estadística.

### Exemples de Consultes per Naturalezas

### Obtenir totes les naturalezas
```
GET /natures/_search
```

### Buscar una naturalesa per nom
```
GET /natures/_search
{
  "query": {
    "term": {
      "name.keyword": "adamant"
    }
  }
}
```

### Buscar naturalezas que augmenten una estadística específica
```
GET /natures/_search
{
  "query": {
    "term": {
      "increased_stat": "attack"
    }
  }
}
```

### Buscar naturalezas neutrals (que no modifiquen estadístiques)
```
GET /natures/_search
{
  "query": {
    "bool": {
      "must_not": [
        {"exists": {"field": "increased_stat"}}
      ]
    }
  }
}
```

## Estructura de l'Índex `users`

L'índex `users` conté la informació de tots els usuaris registrats al sistema:

- **`user_id`**: ID únic de l'usuari (integer)
- **`username`**: Nom d'usuari (text amb keyword per a cerques exactes)
- **`email`**: Adreça de correu electrònic (keyword, únic)
- **`password_hash`**: Hash de la contrasenya (keyword, mai guardar contrasenyes en text pla)
- **`created_at`**: Data de creació del compte (date)
- **`updated_at`**: Data de última actualització (date)
- **`is_active`**: Indica si el compte està actiu (boolean)
- **`profile`**: Objecte amb informació del perfil:
  - `full_name`: Nom complet de l'usuari (text)
  - `avatar_url`: URL de l'avatar (keyword)
  - `bio`: Biografia de l'usuari (text)
  - `favorite_pokemon`: Pokémon favorit de l'usuari (keyword)
- **`preferences`**: Objecte amb preferències de l'usuari:
  - `default_format`: Format per defecte (ex: "vgc", "smogon") (keyword)
  - `language`: Idioma preferit (keyword)
  - `theme`: Tema de la interfície (keyword)

**Nota:** Els usuaris es creen dinàmicament quan es registren al sistema. També pots utilitzar l'script `ingesta_usuarios.py` per crear els usuaris predefinits (jordi_bolance, jordi_barnola, pol_torrent, jordi_roura, marc_cassanmagnago). L'script `ingesta_completa.py` executarà automàticament aquest script si no troba cap usuari a la base de dades.

### Crear Usuaris via Kibana

Pots crear usuaris directament des de **Kibana Dev Tools** utilitzant les comandes del fitxer `crear-usuari-prova.json`.

**Pasos:**

1. Obre Kibana i ves a **Dev Tools** (des del menú lateral)
2. Copia i enganxa una de les comandes del fitxer `crear-usuari-prova.json`
3. Clica el botó **▶** per executar la comanda

**Exemple bàsic:**

```json
POST /users/_doc/1
{
  "user_id": 1,
  "username": "jordi_bolance",
  "email": "jordi@example.com",
  "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqBWVHxkd0",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "is_active": true
}
```

**⚠️ Important sobre contrasenyes:**

Mai guardis contrasenyes en text pla! Sempre utilitza un hash. Per generar un hash de contrasenya en Python:

```python
import bcrypt

password = "mi_contraseña_segura"
password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
print(password_hash)
```

També pots utilitzar la data actual automàticament:

```json
POST /users/_doc/1
{
  "user_id": 1,
  "username": "jordi_bolance",
  "email": "jordi@example.com",
  "password_hash": "$2b$12$...",
  "created_at": "now",
  "updated_at": "now",
  "is_active": true
}
```

### Exemples de Consultes per Usuaris

### Obtenir tots els usuaris
```
GET /users/_search
```

### Buscar un usuari per nom d'usuari
```
GET /users/_search
{
  "query": {
    "term": {
      "username.keyword": "jordi_bolance"
    }
  }
}
```

### Buscar un usuari per email
```
GET /users/_search
{
  "query": {
    "term": {
      "email": "jordi@example.com"
    }
  }
}
```

### Buscar usuaris actius
```
GET /users/_search
{
  "query": {
    "term": {
      "is_active": true
    }
  }
}
```

### Buscar usuaris amb un Pokémon favorit específic
```
GET /users/_search
{
  "query": {
    "term": {
      "profile.favorite_pokemon": "pikachu"
    }
  }
}
```

### Eliminar un usuari

Per eliminar un usuari, necessites conèixer el seu ID del document (el que vas utilitzar quan el vas crear, per exemple `1`, `2`, `3`, etc.).

**Opció 1: Eliminar per ID del document (recomanat)**

```json
DELETE /users/_doc/1
```

Això elimina l'usuari amb ID de document `1`.

**Opció 2: Eliminar per user_id (si coneixes el user_id però no l'ID del document)**

Primer busca l'ID del document:

```json
GET /users/_search
{
  "query": {
    "term": {
      "user_id": 1
    }
  }
}
```

Després, utilitza l'`_id` que apareix a la resposta per eliminar-lo:

```json
DELETE /users/_doc/[ID_DEL_DOCUMENT]
```

**Opció 3: Eliminar múltiples usuaris amb una consulta**

```json
POST /users/_delete_by_query
{
  "query": {
    "term": {
      "user_id": 1
    }
  }
}
```

Això elimina tots els usuaris que tinguin `user_id` igual a `1`.

**⚠️ Important:**
- L'operació DELETE és permanent i no es pot desfer
- Si l'usuari té equips associats, considera eliminar-los primer o actualitzar-los
- Després d'eliminar, el document desapareix immediatament de l'índex

