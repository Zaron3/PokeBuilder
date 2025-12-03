# Guia d'Ús de Kibana - PokeBuilder

## 🚀 Accedir a Kibana

### 1. Verificar que els contenedors estan funcionant

```powershell
docker ps
```

Hauries de veure:
- `kb-container` (Kibana) al port **5601**
- `es-container` (Elasticsearch) al port **9200**

### 2. Obrir Kibana al navegador

Obre el teu navegador i vés a:

**http://localhost:5601**

Si és la primera vegada, pot trigar uns segons a carregar. Quan estigui llest, veuràs la pantalla d'inici de Kibana.

---

## 📊 Consultes a Kibana Dev Tools

### Accedir a Dev Tools

1. Al menú lateral esquerre, busca **"Dev Tools"** (icona de clau anglesa/enginy)
2. Clica-hi per obrir la consola de consultes

Ara pots executar consultes directament!

---

## 🔍 Consultes Bàsiques

### 1. Verificar que Elasticsearch funciona

```json
GET /
```

Això retorna informació sobre Elasticsearch.

---

### 2. Llistar tots els índexs disponibles

```json
GET /_cat/indices?v
```

Això mostra tots els índexs amb el nombre de documents.

---

### 3. Comptar documents de cada índex

**Pokémon:**
```json
GET /pokemon/_count
```

**Tipus:**
```json
GET /types/_count
```

**Moviments:**
```json
GET /moves/_count
```

**Items:**
```json
GET /items/_count
```

**Habilitats:**
```json
GET /abilities/_count
```

**Equips:**
```json
GET /teams/_count
```

---

## 🐾 Consultes de Pokémon

### Obtenir tots els Pokémon (primeres 10)

```json
GET /pokemon/_search
{
  "size": 10
}
```

### Buscar un Pokémon per ID

```json
GET /pokemon/_search
{
  "query": {
    "term": {
      "pokedex_id": 25
    }
  }
}
```

### Buscar un Pokémon per nom

```json
GET /pokemon/_search
{
  "query": {
    "match": {
      "name": "pikachu"
    }
  }
}
```

### Buscar Pokémon per tipus

```json
GET /pokemon/_search
{
  "query": {
    "term": {
      "types": "fire"
    }
  }
}
```

### Buscar Pokémon amb habilitat específica

```json
GET /pokemon/_search
{
  "query": {
    "nested": {
      "path": "abilities",
      "query": {
        "term": {
          "abilities.name": "blaze"
        }
      }
    }
  }
}
```

### Buscar Pokémon amb moviment específic

```json
GET /pokemon/_search
{
  "query": {
    "nested": {
      "path": "moves_pool",
      "query": {
        "term": {
          "moves_pool.name": "flamethrower"
        }
      }
    }
  }
}
```

### Ordenar Pokémon per estadística (ex: velocitat)

```json
GET /pokemon/_search
{
  "sort": [
    {
      "stats.speed": {
        "order": "desc"
      }
    }
  ],
  "size": 10
}
```

### Buscar Pokémon PERMESOS en competitivo (no prohibits)

```json
GET /pokemon/_search
{
  "query": {
    "term": {
      "is_banned": false
    }
  },
  "size": 20
}
```

### Buscar Pokémon PROHIBITS en competitivo

```json
GET /pokemon/_search
{
  "query": {
    "term": {
      "is_banned": true
    }
  },
  "size": 20
}
```

### Buscar Pokémon de tipus Fire PERMESOS en competitivo

```json
GET /pokemon/_search
{
  "query": {
    "bool": {
      "must": [
        {
          "term": {
            "types": "fire"
          }
        },
        {
          "term": {
            "is_banned": false
          }
        }
      ]
    }
  },
  "size": 20
}
```

---

## 🔥 Consultes de Tipus

### Obtenir tots els tipus

```json
GET /types/_search
```

### Buscar un tipus específic

```json
GET /types/_search
{
  "query": {
    "term": {
      "name.keyword": "fire"
    }
  }
}
```

### Trobar tipus efectius contra un tipus (ex: water)

```json
GET /types/_search
{
  "query": {
    "term": {
      "double_damage_to": "water"
    }
  }
}
```

### Trobar debilitats d'un tipus (ex: fire)

```json
GET /types/_search
{
  "query": {
    "term": {
      "name.keyword": "fire"
    }
  }
}
```

Això retornarà les debilitats a `double_damage_from`.

---

## ⚔️ Consultes de Moviments

### Obtenir tots els moviments (primeres 20)

```json
GET /moves/_search
{
  "size": 20
}
```

### Buscar moviments d'un tipus específic

```json
GET /moves/_search
{
  "query": {
    "term": {
      "type": "fire"
    }
  },
  "size": 10
}
```

### Buscar moviments físics amb poder > 100

```json
GET /moves/_search
{
  "query": {
    "bool": {
      "must": [
        {
          "term": {
            "category": "physical"
          }
        },
        {
          "range": {
            "power": {
              "gt": 100
            }
          }
        }
      ]
    }
  }
}
```

### Buscar un moviment per nom

```json
GET /moves/_search
{
  "query": {
    "match": {
      "name": "thunderbolt"
    }
  }
}
```

### Buscar moviments d'estat (sense poder)

```json
GET /moves/_search
{
  "query": {
    "term": {
      "category": "status"
    }
  },
  "size": 20
}
```

---

## 🎒 Consultes d'Items/Objectes

### Obtenir tots els items (primeres 20)

```json
GET /items/_search
{
  "size": 20
}
```

### Buscar items d'una categoria específica

```json
GET /items/_search
{
  "query": {
    "match": {
      "category": "held-items"
    }
  },
  "size": 10
}
```

### Buscar un item per nom

```json
GET /items/_search
{
  "query": {
    "match": {
      "name": "master-ball"
    }
  }
}
```

### Buscar items amb un atribut específic

```json
GET /items/_search
{
  "query": {
    "term": {
      "attributes": "holdable"
    }
  },
  "size": 20
}
```

### Buscar items per rang de preu

```json
GET /items/_search
{
  "query": {
    "range": {
      "cost": {
        "gte": 1000,
        "lte": 5000
      }
    }
  }
}
```

### Buscar items de categories específiques (ex: Pokéballs)

```json
GET /items/_search
{
  "query": {
    "match": {
      "category": "standard-balls"
    }
  },
  "size": 20
}
```

### Buscar items de medicina

```json
GET /items/_search
{
  "query": {
    "match": {
      "category": "medicine"
    }
  },
  "size": 20
}
```

### Buscar items que es poden portar (holdable)

```json
GET /items/_search
{
  "query": {
    "term": {
      "attributes": "holdable"
    }
  },
  "size": 30
}
```

### Exemple: Buscar "Leftovers"

```json
GET /items/_search
{
  "query": {
    "match": {
      "name": "leftovers"
    }
  }
}
```

### Exemple: Buscar items que continguin "berry" al nom

```json
GET /items/_search
{
  "query": {
    "wildcard": {
      "name": "*berry*"
    }
  },
  "size": 50
}
```

---

## ⚡ Consultes d'Habilitats

### Obtenir totes les habilitats (primeres 20)

```json
GET /abilities/_search
{
  "size": 20
}
```

### Buscar una habilitat per nom

```json
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

```json
GET /abilities/_search
{
  "query": {
    "match": {
      "generation": "generation-iii"
    }
  },
  "size": 30
}
```

### Buscar habilitats per text a la descripció

```json
GET /abilities/_search
{
  "query": {
    "match": {
      "description": "attack"
    }
  }
}
```

### Exemple: Buscar habilitat "Blaze"

```json
GET /abilities/_search
{
  "query": {
    "term": {
      "name.keyword": "blaze"
    }
  }
}
```

### Exemple: Buscar habilitat "Intimidate"

```json
GET /abilities/_search
{
  "query": {
    "term": {
      "name.keyword": "intimidate"
    }
  }
}
```

### Buscar habilitats de la tercera generació

```json
GET /abilities/_search
{
  "query": {
    "match": {
      "generation": "generation-iii"
    }
  },
  "size": 50
}
```

### Buscar habilitats que continguin "speed" a la descripció

```json
GET /abilities/_search
{
  "query": {
    "match": {
      "description": "speed"
    }
  },
  "size": 20
}
```

### Buscar habilitats que milloren atac

```json
GET /abilities/_search
{
  "query": {
    "match": {
      "effect": "attack"
    }
  },
  "size": 20
}
```

---

## 👥 Consultes d'Equips

### Obtenir tots els equips

```json
GET /teams/_search
```

### Buscar equips d'un usuari

```json
GET /teams/_search
{
  "query": {
    "term": {
      "user_id": "jordi_bolance_test"
    }
  }
}
```

### Buscar equips amb un format específic

```json
GET /teams/_search
{
  "query": {
    "term": {
      "format": "VGC Reg G"
    }
  }
}
```

---

## 💡 Consells Útils

### Veure només certs camps

```json
GET /pokemon/_search
{
  "_source": ["pokedex_id", "name", "types"],
  "size": 5
}
```

### Veure un document específic per ID

```json
GET /pokemon/_doc/25
```

### Fer una cerca amb múltiples condicions

```json
GET /pokemon/_search
{
  "query": {
    "bool": {
      "must": [
        {
          "term": {
            "types": "fire"
          }
        },
        {
          "range": {
            "stats.speed": {
              "gte": 100
            }
          }
        }
      ]
    }
  }
}
```

Això busca Pokémon de tipus Fire amb velocitat >= 100.

---

## 🎯 Consultes Avançades

### Agrupar per tipus (agregació)

```json
GET /pokemon/_search
{
  "size": 0,
  "aggs": {
    "tipus_mes_comuns": {
      "terms": {
        "field": "types",
        "size": 10
      }
    }
  }
}
```

### Estadístiques mitjanes per tipus

```json
GET /pokemon/_search
{
  "size": 0,
  "aggs": {
    "per_tipus": {
      "terms": {
        "field": "types"
      },
      "aggs": {
        "velocitat_mitjana": {
          "avg": {
            "field": "stats.speed"
          }
        }
      }
    }
  }
}
```

---

## 📝 Notes

- Per executar una consulta, clica el botó **"▶"** (play) o prem `Ctrl+Enter`
- Pots tenir múltiples consultes obertes alhora
- Les consultes es guarden automàticament al navegador
- Pots exportar/importar consultes des del menú de Dev Tools

---

**Fet amb ❤️ pel PokeBuilder Team**

