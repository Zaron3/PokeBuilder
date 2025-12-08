# 🧠 PokeBuilder

**PokeBuilder** és un *team builder* de Pokémon competitiu potenciat amb una Intel·ligència Artificial de recomanació.  
Aquest és un projecte universitari.

---

## 📋 Prerequisits

Abans de començar, assegura't de tenir instal·lat el següent programari al teu equip:

- Git
- Docker Desktop
- Python 3.x
- Un IDE recomanat:
    - IntelliJ IDEA
    - PyCharm
    - VS Code

---

## 🚀 Instal·lació i Posada en Marxa

Segueix aquests passos en ordre per aixecar tot l'entorn.

---

### 1️⃣ Clonar el repositori

Obre el teu terminal o IDE i clona el projecte:

```bash
git clone <URL_DEL_TEU_REPOSITORI>
cd pokebuilder
```


## 2️⃣ Base de Dades i Entorn (Docker)

Assegura't que **Docker Desktop està obert i funcionant**.

Des de l’arrel del projecte, executa:

```bash
docker-compose up -d
```
(Això descarregarà i aixecarà els contenidors d'Elasticsearch i Kibana).

Espera uns instants a que arrenquin. Pots comprovar que Kibana funciona anant a:
http://localhost:5601


---

## 3️⃣ Configuració dels Índexs (Kibana)

1. Obre el fitxer del projecte:

scripts-bd/crear-indexs.json

2. Copia tot el seu contingut.
3. Ves al navegador a:

http://localhost:5601/app/dev_tools#/console

(Kibana Dev Tools)
4. Enganxa el contingut a la consola de l'esquerra.
5. Prem el botó **Play** (o `Ctrl + Enter`) per crear l'estructura de la base de dades.

---

## 4️⃣ Ingesta de Dades

Ara cal omplir la base de dades amb la informació dels Pokémon.

> ⚠️ Nota: Assegura't de tenir la llibreria d’elasticsearch instal·lada per aquest script.  
Si falla, executa:
```bash
pip install "elasticsearch<9.0.0"
```

Des de l’arrel del projecte al terminal:
```bash
python scripts-bd/ingesta_completa.py
```

---

## 5️⃣ Microservei d’IA

Aquest servei s'encarrega de les recomanacions.  
Obre un **nou terminal** per mantenir aquest procés actiu.

Navega a la carpeta de la IA:

```bash
cd backend/ia
```
Instal·la les dependències:

```bash
pip install fastapi "uvicorn[standard]" "elasticsearch<9.0.0"
```

Executa el servei:

```bash
python3 ai_service.py
```

Hauries de veure el missatge: ✓ Servei d'IA inicialitzat correctament i INFO: Uvicorn running on http://127.0.0.1:8000.

---

## 6️⃣ Backend Principal (API)

Obre **un altre terminal nou**. Aquest serà el nucli de l'aplicació.

Navega a la carpeta del backend:

```bash
cd backend
```
Instal·la totes les dependències necessàries:

```bash
pip install fastapi "uvicorn[standard]" "elasticsearch<9.0.0" "passlib[bcrypt]" "bcrypt==4.0.1" "python-jose[cryptography]" python-multipart email-validator
```

(Si durant l'execució et falta alguna llibreria extra, el terminal t'avisarà. Instal·la-la amb pip install nom_llibreria).

Aixeca el servidor:

```bash
uvicorn main:app --reload
```

Si la comanda anterior no et funciona, prova amb:

```bash
python -m uvicorn main:app --reload
```

## 7️⃣ Frontend (Client)

Finalment, per utilitzar l'aplicació:

1. Ves a la carpeta:

frontend

2. Obre el fitxer: index.html directament amb el teu navegador web.

🦊 **Recomanació:** Utilitzar **Mozilla Firefox** per a una millor compatibilitat.

---

## 🛠️ Resolució de Problemes Comuns

### ❌ Falten llibreries de Python

Si algun script falla amb l’error: Module not found

Executa:

```bash
pip install <nom_del_modul>
```

i torna-ho a provar.

Docker no connecta: Assegura't que tens Docker Desktop obert i que els ports 9200 (Elasticsearch) i 5601 (Kibana) estan lliures.