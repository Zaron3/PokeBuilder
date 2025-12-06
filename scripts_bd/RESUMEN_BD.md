# Resumen Completo de la Base de Datos - PokeBuilder

## 📊 Índices Disponibles

La base de datos Elasticsearch contiene los siguientes índices:

| Índice | Descripción | Documentos |
|--------|-------------|------------|
| `pokemon` | Información de todos los Pokémon | **1,025** |
| `types` | Tipos de Pokémon y relaciones de efectividad | **20** |
| `moves` | Movimientos de Pokémon | **937** |
| `items` | Objetos/Items de Pokémon | **2,180** |
| `abilities` | Habilidades de Pokémon | **367** |
| `natures` | Naturalezas de Pokémon | **25** |
| `users` | Usuarios registrados en el sistema | **5** (variable) |
| `teams` | Equipos creados por usuarios | **0** (variable) |

---

## 🐾 Índice: `pokemon`

### Descripción
Contiene la información completa de todos los Pokémon disponibles.

### Campos Principales

#### Información Básica
- **`pokedex_id`** (integer): ID numérico del Pokémon en la Pokédex
- **`name`** (text/keyword): Nombre del Pokémon (ej: "pikachu", "charizard")
- **`types`** (keyword[]): Lista de tipos del Pokémon (ej: ["fire", "flying"])

#### Estadísticas
- **`stats`** (object): Objeto con las estadísticas base:
  - `hp` (integer): Puntos de salud
  - `attack` (integer): Ataque físico
  - `defense` (integer): Defensa física
  - `special_attack` (integer): Ataque especial
  - `special_defense` (integer): Defensa especial
  - `speed` (integer): Velocidad

#### Habilidades
- **`abilities`** (nested[]): Array de habilidades disponibles:
  - `name` (keyword): Nombre de la habilidad
  - `is_hidden` (boolean): Si es una habilidad oculta

#### Movimientos
- **`moves_pool`** (nested[]): Pool de movimientos que puede aprender:
  - `name` (keyword): Nombre del movimiento
  - `learn_method` (keyword): Método de aprendizaje (ej: "level-up", "tm", "hm")

#### Competitivo
- **`is_banned`** (boolean): Indica si el Pokémon está prohibido en competitivo
  - `false`: Permitido en competitivo
  - `true`: Prohibido (légendarios, míticos, etc.)

### Ejemplo de Documento
```json
{
  "pokedex_id": 25,
  "name": "pikachu",
  "types": ["electric"],
  "stats": {
    "hp": 35,
    "attack": 55,
    "defense": 40,
    "special_attack": 50,
    "special_defense": 50,
    "speed": 90
  },
  "abilities": [
    {"name": "static", "is_hidden": false},
    {"name": "lightning-rod", "is_hidden": true}
  ],
  "moves_pool": [
    {"name": "thunder-shock", "learn_method": "level-up"},
    {"name": "quick-attack", "learn_method": "level-up"}
  ],
  "is_banned": false
}
```

---

## 🔥 Índice: `types`

### Descripción
Contiene información sobre los tipos de Pokémon y sus relaciones de efectividad (tabla de tipos).

### Campos Principales

- **`type_id`** (integer): ID numérico del tipo
- **`name`** (text/keyword): Nombre del tipo (ej: "fire", "water", "grass")
- **`double_damage_from`** (keyword[]): Tipos que hacen doble daño a este tipo (debilidades)
- **`half_damage_from`** (keyword[]): Tipos que hacen medio daño a este tipo (resistencias)
- **`no_damage_from`** (keyword[]): Tipos que no hacen daño a este tipo (inmunidades)
- **`double_damage_to`** (keyword[]): Tipos a los que este tipo hace doble daño (fortalezas)
- **`half_damage_to`** (keyword[]): Tipos a los que este tipo hace medio daño
- **`no_damage_to`** (keyword[]): Tipos a los que este tipo no hace daño

### Ejemplo de Documento
```json
{
  "type_id": 10,
  "name": "fire",
  "double_damage_from": ["water", "ground", "rock"],
  "half_damage_from": ["fire", "grass", "ice", "bug", "steel", "fairy"],
  "no_damage_from": [],
  "double_damage_to": ["grass", "ice", "bug", "steel"],
  "half_damage_to": ["fire", "water", "rock", "dragon"],
  "no_damage_to": []
}
```

---

## ⚔️ Índice: `moves`

### Descripción
Contiene información completa de todos los movimientos de Pokémon.

### Campos Principales

- **`move_id`** (keyword): ID del movimiento
- **`name`** (text/keyword): Nombre del movimiento (ej: "thunderbolt", "flamethrower")
- **`type`** (keyword): Tipo del movimiento (ej: "electric", "fire")
- **`category`** (keyword): Categoría del movimiento:
  - `"physical"`: Movimiento físico
  - `"special"`: Movimiento especial
  - `"status"`: Movimiento de estado
- **`power`** (integer): Poder del movimiento (0 para movimientos de estado)
- **`accuracy`** (integer): Precisión del movimiento (0-100)
- **`pp`** (integer): Puntos de poder (Power Points)
- **`description`** (text): Descripción del movimiento

### Ejemplo de Documento
```json
{
  "move_id": "85",
  "name": "thunderbolt",
  "type": "electric",
  "category": "special",
  "power": 90,
  "accuracy": 100,
  "pp": 15,
  "description": "A strong electric blast crashes down on the target."
}
```

---

## 🎒 Índice: `items`

### Descripción
Contiene información de todos los objetos/items disponibles en Pokémon.

### Campos Principales

- **`item_id`** (integer): ID numérico del item
- **`name`** (text/keyword): Nombre del item (ej: "potion", "master-ball", "leftovers")
- **`category`** (keyword): Categoría del item:
  - `"standard-balls"`: Pokéballs estándar
  - `"special-balls"`: Pokéballs especiales
  - `"medicine"`: Medicina
  - `"held-items"`: Objetos que se pueden portar
  - `"mega-stones"`: Mega Piedras
  - Y muchas más...
- **`cost`** (integer): Coste del item en Pokédólares
- **`description`** (text): Descripción del item
- **`effect`** (text): Efecto detallado del item
- **`attributes`** (keyword[]): Atributos del item (ej: ["holdable", "consumable"])

### Ejemplo de Documento
```json
{
  "item_id": 4,
  "name": "master-ball",
  "category": "standard-balls",
  "cost": 0,
  "description": "The best Ball with the ultimate level of performance.",
  "effect": "Catches a wild Pokémon without fail.",
  "attributes": []
}
```

---

## ⚡ Índice: `abilities`

### Descripción
Contiene información de todas las habilidades de Pokémon.

### Campos Principales

- **`ability_id`** (integer): ID numérico de la habilidad
- **`name`** (text/keyword): Nombre de la habilidad (ej: "blaze", "intimidate", "overgrow")
- **`description`** (text): Descripción breve de la habilidad
- **`effect`** (text): Efecto detallado de la habilidad
- **`generation`** (keyword): Generación donde apareció por primera vez (ej: "generation-iii")

### Ejemplo de Documento
```json
{
  "ability_id": 66,
  "name": "blaze",
  "description": "Powers up Fire-type moves when the Pokémon's HP is low.",
  "effect": "When this Pokémon has 1/3 or less of its maximum HP, its Fire-type moves have 1.5× their base power.",
  "generation": "generation-iii"
}
```

---

## 🌿 Índice: `natures`

### Descripción
Contiene información de todas las naturalezas de Pokémon que afectan el crecimiento de las estadísticas.

### Campos Principales

- **`nature_id`** (integer): ID numérico de la naturalesa
- **`name`** (text/keyword): Nombre de la naturalesa (ej: "adamant", "modest", "jolly")
- **`increased_stat`** (keyword): Estadística que aumenta en un 10% (ej: "attack", "special-attack", null para neutral)
- **`decreased_stat`** (keyword): Estadística que disminuye en un 10% (ej: "special-attack", "attack", null para neutral)
- **`likes_flavor`** (keyword): Sabor de baya que le gusta (ej: "spicy", "dry", "sweet", "bitter", "sour")
- **`hates_flavor`** (keyword): Sabor de baya que odia (ej: "spicy", "dry", "sweet", "bitter", "sour")

**Nota:** Las naturalezas neutras (como "Hardy", "Docile", etc.) no aumentan ni disminuyen ninguna estadística (`increased_stat` y `decreased_stat` son `null`).

### Ejemplo de Documento
```json
{
  "nature_id": 2,
  "name": "adamant",
  "increased_stat": "attack",
  "decreased_stat": "special-attack",
  "likes_flavor": "spicy",
  "hates_flavor": "dry"
}
```

### Ejemplo de Naturalesa Neutral
```json
{
  "nature_id": 1,
  "name": "hardy",
  "increased_stat": null,
  "decreased_stat": null,
  "likes_flavor": null,
  "hates_flavor": null
}
```

---

## 👥 Índice: `teams`

### Descripción
Contiene los equipos de Pokémon creados por los usuarios.

### Campos Principales

#### Información del Equipo
- **`team_name`** (text/keyword): Nombre del equipo
- **`description`** (text): Descripción del equipo
- **`user_id`** (keyword): ID del usuario que creó el equipo (referencia al índice `users`)
- **`format`** (keyword): Formato competitivo (ej: "VGC Reg G", "OU", "Ubers")

#### Miembros del Equipo
- **`team_members`** (nested[]): Array de Pokémon en el equipo:
  - `base_pokemon` (keyword): Nombre base del Pokémon
  - `nickname` (text): Apodo del Pokémon
  - `item` (keyword): Objeto equipado
  - `ability` (keyword): Habilidad seleccionada
  - `tera_type` (keyword): Tipo Teracristalización
  - `nature` (keyword): Naturaleza del Pokémon
  - `moves` (keyword[]): Lista de movimientos (4 movimientos)
  - `evs` (object): Distribución de EVs:
    - `hp` (short)
    - `attack` (short)
    - `defense` (short)
    - `sp_atk` (short)
    - `sp_def` (short)
    - `speed` (short)

### Ejemplo de Documento
```json
{
  "team_name": "Equip de Sol VGC",
  "description": "Equip VGC basat en Sol",
  "user_id": "jordi_bolance_test",
  "format": "VGC Reg G",
  "team_members": [
    {
      "base_pokemon": "Torkoal",
      "nickname": "Volcano",
      "item": "Charcoal",
      "ability": "Drought",
      "tera_type": "Fire",
      "nature": "Quiet",
      "moves": ["Eruption", "Heat Wave", "Protect", "Earth Power"],
      "evs": {
        "hp": 252,
        "attack": 0,
        "defense": 0,
        "sp_atk": 252,
        "sp_def": 4,
        "speed": 0
      }
    }
  ]
}
```

---

## 👤 Índice: `users`

### Descripción
Contiene la información de todos los usuarios registrados en el sistema.

### Campos Principales

#### Información Básica
- **`user_id`** (integer): ID único numérico del usuario
- **`username`** (text/keyword): Nombre de usuario (ej: "jordi_bolance")
- **`email`** (keyword): Dirección de correo electrónico (único)
- **`password_hash`** (keyword): Hash de la contraseña (nunca en texto plano)
- **`created_at`** (date): Fecha de creación del cuenta
- **`updated_at`** (date): Fecha de última actualización
- **`is_active`** (boolean): Indica si el cuenta está activo

#### Perfil del Usuario
- **`profile`** (object): Objeto con información del perfil:
  - `full_name` (text): Nombre completo del usuario
  - `avatar_url` (keyword): URL del avatar
  - `bio` (text): Biografía del usuario
  - `favorite_pokemon` (keyword): Pokémon favorito del usuario

#### Preferencias
- **`preferences`** (object): Objeto con preferencias del usuario:
  - `default_format` (keyword): Formato por defecto (ej: "vgc", "smogon")
  - `language` (keyword): Idioma preferido (ej: "ca", "es", "en")
  - `theme` (keyword): Tema de la interfaz (ej: "dark", "light")

### Ejemplo de Documento
```json
{
  "user_id": 1,
  "username": "jordi_bolance",
  "email": "jordi.bolance@example.com",
  "password_hash": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYqBWVHxkd0",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z",
  "is_active": true,
  "profile": {
    "full_name": "Jordi Bolance",
    "avatar_url": "https://example.com/avatar.jpg",
    "bio": "Entusiasta de Pokémon competitivo",
    "favorite_pokemon": "pikachu"
  },
  "preferences": {
    "default_format": "vgc",
    "language": "ca",
    "theme": "dark"
  }
}
```

### Usuarios Predefinidos
El sistema incluye 5 usuarios predefinidos que se pueden crear ejecutando `ingesta_usuarios.py`:
- `jordi_bolance` (user_id: 1)
- `jordi_barnola` (user_id: 2)
- `pol_torrent` (user_id: 3)
- `jordi_roura` (user_id: 4)
- `marc_cassanmagnago` (user_id: 5)

---

## 📈 Estadísticas Generales

### Total de Documentos por Índice

- **Pokémon**: **1,025** documentos
- **Tipos**: **20** documentos
- **Movimientos**: **937** documentos
- **Items**: **2,180** documentos
- **Habilidades**: **367** documentos
- **Naturalezas**: **25** documentos
- **Usuarios**: **5** documentos (se pueden crear más dinámicamente)
- **Equipos**: **0** documentos (se crean dinámicamente)

### Total Real
**4,559 documentos** en total (sin contar equipos que son variables)

---

## 🔍 Consultas Útiles

### Contar documentos de cada índice
```json
GET /pokemon/_count
GET /types/_count
GET /moves/_count
GET /items/_count
GET /abilities/_count
GET /natures/_count
GET /users/_count
GET /teams/_count
```

### Ver todos los índices
```json
GET /_cat/indices?v
```

### Ver estructura de un documento
```json
GET /pokemon/_doc/25
GET /types/_doc/10
GET /moves/_doc/85
GET /users/_doc/1
```

---

## 📝 Notas Importantes

1. **Pokémon prohibidos**: El campo `is_banned` indica si un Pokémon está prohibido en competitivo. Se puede actualizar ejecutando `marcar_pokemon_prohibits.py`.

2. **Relaciones**: 
   - Los Pokémon tienen referencias a tipos, habilidades y movimientos por nombre
   - Los equipos referencian usuarios por `user_id` (integer) y Pokémon por nombre base
   - Los usuarios pueden tener múltiples equipos asociados
   - No hay claves foráneas explícitas, se usa búsqueda por nombre o ID

3. **Actualización**: Los datos se pueden actualizar ejecutando los scripts de ingesta correspondientes.

4. **Formato de nombres**: Todos los nombres están en minúsculas y con guiones (ej: "master-ball", "thunder-shock").

---

**Última actualización**: Generado automáticamente
**Versión de Elasticsearch**: 8.10.4

