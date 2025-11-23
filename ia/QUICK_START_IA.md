# Guia Ràpida - Sistema de IA de PokeBuilder

## 🚀 Inici Ràpid en 5 Passos

### 1. Verificar Prerequisits

Assegura't que tens:
- ✅ Python 3.7+
- ✅ Elasticsearch 8.x funcionant a `localhost:9200`
- ✅ Dades carregades (índexs `pokemon` i `types`)

**Comprovar Elasticsearch:**
```bash
curl http://localhost:9200
```

### 2. Instal·lar Dependències

```bash
cd backend
pip install fastapi "uvicorn[standard]" "elasticsearch<9.0.0"
```

### 3. Provar el Sistema d'IA

```bash
cd ia
python3 ai_service.py
```

Si funciona, veuràs:
```
✓ Carregats 18 tipus
✓ Servei inicialitzat
✓ Test completat amb èxit!
```

### 4. Iniciar el Backend

```bash
cd backend
uvicorn main:app --reload
```

Hauries de veure:
```
✓ Servei d'IA inicialitzat correctament
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### 5. Obrir el Frontend

Obre `frontend/index.html` al navegador i:
1. Afegeix alguns Pokémon a l'equip
2. Clica "Recomanar Pokémon"
3. Veuràs la recomanació amb explicació detallada!

---

## 🧪 Provar l'API Directament

### Comprovar estat:
```bash
curl http://localhost:8000/api/v1/ai/status
```

### Obtenir recomanació:
```bash
curl -X POST http://localhost:8000/api/v1/ai/recommend \
  -H "Content-Type: application/json" \
  -d '{"team_ids": [1, 4, 7]}'
```

### Analitzar equip:
```bash
curl -X POST http://localhost:8000/api/v1/ai/analyze \
  -H "Content-Type: application/json" \
  -d '{"team_ids": [1, 4, 7]}'
```

---

## 📚 Documentació Completa

Per a més detalls, consulta:
- **DOCUMENTACIO_IA.md**: Documentació completa del sistema
- **ia/README.md**: Documentació tècnica del mòdul d'IA
- **http://localhost:8000/docs**: Documentació interactiva de l'API

---

## ❓ Problemes Comuns

### Error: "El servei d'IA no està disponible"

**Solució:**
1. Verifica que Elasticsearch està funcionant
2. Comprova que els índexs estan carregats:
   ```bash
   curl http://localhost:9200/pokemon/_count
   curl http://localhost:9200/types/_count
   ```
3. Reinicia el backend

### Error: "No s'han carregat tipus"

**Solució:**
Carrega les dades de tipus:
```bash
cd scripts_bd
python3 ingesta_tipus.py
```

### Error: "Connection refused"

**Solució:**
Inicia Elasticsearch:
```bash
docker-compose up -d elasticsearch
```

---

## 🎯 Exemples d'Ús

### Equip amb Debilitat a Electric
```json
{"team_ids": [7, 130, 144]}
```
→ Recomana Pokémon Ground (immune a Electric)

### Equip Mono-Fire
```json
{"team_ids": [4, 37, 58]}
```
→ Recomana Pokémon Water/Rock per cobrir debilitats

### Equip Equilibrat
```json
{"team_ids": [25, 94, 143, 248]}
```
→ Recomana Pokémon que complementi l'equip

---

## 📞 Suport

Per a més informació o problemes, consulta la documentació completa o revisa els logs del backend.

**Logs útils:**
- Backend: Terminal on executes `uvicorn`
- Frontend: Consola del navegador (F12)

---

**Fet amb ❤️ pel PokeBuilder Team**
