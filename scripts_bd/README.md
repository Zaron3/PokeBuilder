# Scripts de Base de Dades - PokeBuilder

Aquest directori conté els scripts necessaris per configurar i poblar la base de dades Elasticsearch del projecte PokeBuilder.

## Estructura de Fitxers

### Configuració d'Índexs
- **`crear-indexs.json`**: Script per crear tots els índexs d'Elasticsearch (pokemon, moves, teams, types)

### Scripts d'Ingesta
- **`ingesta_completa.py`**: ⭐ **Script intel·ligent** que executa només els scripts necessaris (verifica quins índexs tenen dades)
- **`ingesta_pokemon.py`**: Importa dades de Pokémon des de PokéAPI a Elasticsearch (inclou abilities, moves_pool i is_banned)
- **`ingesta_tipus.py`**: Importa tots els tipus de Pokémon amb les seves relacions d'efectivitat des de PokéAPI
- **`ingesta_moves.py`**: Importa tots els moviments de Pokémon des de PokéAPI a Elasticsearch
- **`ingesta_items.py`**: Importa tots els items/objectes de Pokémon des de PokéAPI a Elasticsearch
- **`ingesta_abilities.py`**: Importa totes les habilitats de Pokémon des de PokéAPI a Elasticsearch
- **`ingesta_natures.py`**: Importa totes les naturalezas de Pokémon des de PokéAPI a Elasticsearch
- **`marcar_pokemon_prohibits.py`**: Marca els Pokémon prohibits en competitivo (llegendaris, míticos, etc.)

### Dades de Prova
- **`llista-pokemon-prova.json`**: Exemples de Pokémon per a proves
- **`llista-tipus-prova.json`**: Exemples de tipus amb relacions d'efectivitat per a proves
- **`crear-equip-prova.json`**: Exemple d'equip complet per a proves

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
- ✅ Demana confirmació abans d'executar
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

### 9. Dades de Prova

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

