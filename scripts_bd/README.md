# Scripts de Base de Dades - PokeBuilder

Aquest directori conté els scripts necessaris per configurar i poblar la base de dades Elasticsearch del projecte PokeBuilder.

## Estructura de Fitxers

### Configuració d'Índexs
- **`crear-indexs.json`**: Script per crear tots els índexs d'Elasticsearch (pokemon, moves, teams, types)

### Scripts d'Ingesta
- **`ingesta.py`**: Importa dades de Pokémon des de PokéAPI a Elasticsearch
- **`ingesta_tipus.py`**: Importa tots els tipus de Pokémon amb les seves relacions d'efectivitat des de PokéAPI

### Dades de Prova
- **`llista-pokemon-prova.json`**: Exemples de Pokémon per a proves
- **`llista-tipus-prova.json`**: Exemples de tipus amb relacions d'efectivitat per a proves
- **`crear-equip-prova.json`**: Exemple d'equip complet per a proves

## Ús

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
python ingesta.py
```

Per defecte, importa els Pokémon amb IDs del 1 al 9. Pots modificar el rang a l'script.

### 4. Dades de Prova

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

