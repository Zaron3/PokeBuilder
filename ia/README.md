# Sistema de Recomanació IA - PokeBuilder

Aquest directori conté el sistema de recomanació intel·ligent per a PokeBuilder, que analitza equips de Pokémon i suggereix candidats òptims basant-se en múltiples criteris.

## Arquitectura

### Mòduls Principals

#### 1. `recommendation_engine.py`
Motor principal de recomanació que implementa l'algoritme d'avaluació.

**Classes principals:**
- `Pokemon`: Dataclass que representa un Pokémon
- `TypeEffectiveness`: Dataclass amb informació d'efectivitat de tipus
- `Recommendation`: Dataclass amb una recomanació i el seu raonament
- `RecommendationEngine`: Motor que calcula puntuacions i genera recomanacions

**Funcionalitats:**
- Anàlisi d'equips (debilitats, resistències, estadístiques)
- Càlcul de puntuacions per a candidats
- Generació de raonament explicatiu

#### 2. `ai_service.py`
Servei que connecta el motor de recomanació amb Elasticsearch.

**Funcionalitats:**
- Connexió amb Elasticsearch
- Càrrega de dades de tipus i Pokémon
- Interfície d'alt nivell per a recomanacions
- Anàlisi d'equips

## Algoritme de Recomanació

El sistema avalua cada Pokémon candidat segons 4 criteris principals:

### 1. Cobertura Defensiva (40%)
Avalua com el candidat cobreix les debilitats de l'equip actual.

**Bonificacions:**
- +10 punts per cada tipus al qual resisteix que sigui una debilitat de l'equip
- +15 punts per cada tipus al qual és immune que sigui una debilitat de l'equip

**Penalitzacions:**
- -5 punts per cada debilitat compartida amb l'equip

### 2. Cobertura Ofensiva (25%)
Avalua la diversitat de tipus ofensius.

**Bonificacions:**
- +15 punts per cada tipus ofensiu nou que aporta
- +5 punts per cada tipus comú contra el qual és efectiu

**Penalitzacions:**
- -5 punts per redundància de tipus

### 3. Diversitat de Tipus (20%)
Avalua la varietat de tipus a l'equip.

**Bonificacions:**
- +30 punts si aporta dos tipus nous
- +20 punts si aporta un tipus nou
- +10 punts si té doble tipus (versatilitat)

**Penalitzacions:**
- -10 punts si els tipus ja estan presents

### 4. Equilibri d'Estadístiques (15%)
Avalua com complementa les estadístiques de l'equip.

**Bonificacions:**
- +10 punts per cada estadística alta que complementa una baixa de l'equip
- +5 punts per estadístiques excel·lents (>100)
- +10 punts si el total d'estadístiques base és >500

### Puntuació Final

```
Puntuació = (Defensiva × 0.40) + (Ofensiva × 0.25) + (Diversitat × 0.20) + (Estadístiques × 0.15)
```

Totes les puntuacions es normalitzen a l'escala 0-100.

## Ús

### Instal·lació de Dependències

```bash
pip install elasticsearch
```

### Exemple d'Ús

```python
from ai_service import AIService

# Inicialitzar servei
service = AIService()

# Obtenir recomanacions per a un equip
team_ids = [1, 4, 7]  # Bulbasaur, Charmander, Squirtle
recommendations = service.recommend_pokemon(team_ids, top_n=5)

# Mostrar resultats
for rec in recommendations:
    print(f"{rec['name']}: {rec['score']}/100")
    for reason in rec['reasoning']:
        print(f"  • {reason}")
```

### Test del Sistema

Pots executar el test integrat:

```bash
cd ia
python3 ai_service.py
```

Això executarà un test complet que:
1. Inicialitza el servei
2. Carrega dades de tipus i Pokémon
3. Analitza un equip d'exemple
4. Genera recomanacions
5. Mostra els resultats

## Integració amb l'API

El backend (`backend/main.py`) exposa els següents endpoints:

### POST `/api/v1/ai/recommend`
Genera recomanacions per a un equip.

**Request:**
```json
{
  "team_ids": [1, 4, 7]
}
```

**Response:**
```json
{
  "success": true,
  "team_size": 3,
  "recommendations": [
    {
      "pokedex_id": 25,
      "name": "pikachu",
      "types": ["electric"],
      "score": 78.5,
      "scores": {
        "defensive": 65.0,
        "offensive": 80.0,
        "diversity": 90.0,
        "stats": 70.0
      },
      "reasoning": [
        "Afegeix cobertura ofensiva de tipus Electric",
        "Afegeix tipus nou: Electric",
        ...
      ]
    }
  ]
}
```

### POST `/api/v1/ai/analyze`
Analitza un equip i retorna fortaleses i debilitats.

**Request:**
```json
{
  "team_ids": [1, 4, 7]
}
```

**Response:**
```json
{
  "success": true,
  "analysis": {
    "team_size": 3,
    "weaknesses": {
      "fire": 2,
      "flying": 1,
      ...
    },
    "resistances": {
      "water": 2,
      ...
    },
    "immunities": [],
    "type_coverage": ["grass", "poison", "fire", "water"],
    "avg_stats": {
      "hp": 55.0,
      "attack": 60.0,
      ...
    }
  }
}
```

### GET `/api/v1/ai/status`
Comprova l'estat del servei d'IA.

**Response:**
```json
{
  "enabled": true,
  "service_initialized": true,
  "types_loaded": 18
}
```

## Requisits

- Python 3.7+
- Elasticsearch 8.x funcionant a `localhost:9200`
- Índexs `pokemon` i `types` poblats amb dades

## Notes Tècniques

### Pesos del Sistema
Els pesos actuals estan optimitzats per a joc competitiu casual:
- **Defensiva (40%)**: Prioritza cobrir debilitats
- **Ofensiva (25%)**: Assegura diversitat d'atac
- **Diversitat (20%)**: Evita redundància
- **Estadístiques (15%)**: Complementa l'equip

Aquests pesos es poden ajustar a `RecommendationEngine.WEIGHTS`.

### Tipus Comuns
El sistema considera aquests tipus com a "comuns" per a bonificacions ofensives:
- Water, Fire, Grass, Electric, Psychic

Aquesta llista es pot modificar a `_calculate_offensive_score()`.

### Normalització
Totes les puntuacions es normalitzen a 0-100 per facilitar la interpretació i comparació.

## Millores Futures

Possibles extensions del sistema:

1. **Consideració de moviments**: Avaluar el pool de moviments disponibles
2. **Anàlisi de sinergia**: Detectar combinacions específiques (cores)
3. **Metagame awareness**: Ajustar recomanacions segons l'ús actual
4. **Rols específics**: Recomanar segons rol (sweeper, wall, pivot)
5. **Machine Learning**: Entrenar amb dades d'equips competitius reals
6. **Habilitats**: Considerar habilitats dels Pokémon
7. **Items**: Avaluar sinergia amb items competitius

## Autors

PokeBuilder Team - Projecte Universitari 2024

## Llicència

Aquest projecte és part d'un treball universitari.
