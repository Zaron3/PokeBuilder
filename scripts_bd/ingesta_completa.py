"""
Script intel·ligent que executa només els scripts d'ingesta necessaris.
Verifica quins índexs tenen dades i només executa els scripts per a índexs buits o que necessitin actualització.

Executa automàticament sense demanar confirmació.
"""
import requests
import subprocess
import sys
import os

ELASTIC_URL = "http://localhost:9200"

# Mapeig d'índexs als seus scripts d'ingesta
SCRIPTS_INGESTA = {
    "pokemon": "ingesta_pokemon.py",
    "types": "ingesta_tipus.py",
    "moves": "ingesta_moves.py",
    "items": "ingesta_items.py",
    "abilities": "ingesta_abilities.py",
    "natures": "ingesta_natures.py"
}

# Límits mínims esperats per cada índex (si hi ha menys, es considera que cal actualitzar)
LIMITS_MINIMS = {
    "pokemon": 100,      # Esperem almenys 100 Pokémon
    "types": 15,         # Esperem almenys 15 tipus
    "moves": 500,        # Esperem almenys 500 moviments
    "items": 1000,       # Esperem almenys 1000 items
    "abilities": 200,    # Esperem almenys 200 habilitats
    "natures": 20        # Esperem almenys 20 naturalezas
}

def verificar_connexio():
    """Verifica que Elasticsearch està funcionant."""
    try:
        response = requests.get(ELASTIC_URL)
        if response.status_code == 200:
            return True
        return False
    except:
        return False

def verificar_index_existeix(index_name):
    """Verifica si un índex existeix."""
    try:
        response = requests.get(f"{ELASTIC_URL}/{index_name}")
        return response.status_code == 200
    except:
        return False

def comptar_documents(index_name):
    """Compta els documents d'un índex."""
    try:
        if not verificar_index_existeix(index_name):
            return 0
        
        response = requests.get(f"{ELASTIC_URL}/{index_name}/_count")
        if response.status_code == 200:
            return response.json().get('count', 0)
        return 0
    except:
        return 0

def executar_script(script_name):
    """Executa un script d'ingesta."""
    print(f"\n{'='*60}")
    print(f"EXECUTANT: {script_name}")
    print(f"{'='*60}\n")
    
    try:
        # Executem el script amb Python
        result = subprocess.run(
            [sys.executable, script_name],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            print(f"\n✓ Script {script_name} executat amb èxit")
            return True
        else:
            print(f"\n✗ Error executant {script_name} (codi: {result.returncode})")
            return False
    except Exception as e:
        print(f"\n✗ Error executant {script_name}: {e}")
        return False

def main():
    """Funció principal que decideix quins scripts executar."""
    print("\n" + "="*60)
    print("SCRIPT D'INGESTA INTEL·LIGENT - POKEBUILDER")
    print("="*60 + "\n")
    
    # Verificar connexió
    print("1. Verificant connexió amb Elasticsearch...")
    if not verificar_connexio():
        print("✗ ERROR: No es pot connectar a Elasticsearch a localhost:9200")
        print("   Assegura't que Elasticsearch està funcionant.")
        return
    
    print("✓ Elasticsearch està funcionant\n")
    
    # Verificar estat de cada índex
    print("2. Verificant estat dels índexs...\n")
    
    indexos_a_importar = []
    indexos_ok = []
    
    for index_name, script_name in SCRIPTS_INGESTA.items():
        count = comptar_documents(index_name)
        limit_minim = LIMITS_MINIMS.get(index_name, 0)
        
        if count == 0:
            print(f"  ⚠ {index_name:12} : {count:>5} documents → CAL IMPORTAR")
            indexos_a_importar.append((index_name, script_name))
        elif count < limit_minim:
            print(f"  ⚠ {index_name:12} : {count:>5} documents → CAL ACTUALITZAR (mínim esperat: {limit_minim})")
            indexos_a_importar.append((index_name, script_name))
        else:
            print(f"  ✓ {index_name:12} : {count:>5} documents → OK")
            indexos_ok.append((index_name, count))
    
    print()
    
    # Inicialitzar comptadors
    exitosos = 0
    fallits = 0
    
    # Executar scripts d'ingesta si cal
    if indexos_a_importar:
        # Mostrar què s'executarà
        print("="*60)
        print("SCRIPTS QUE S'EXECUTARAN:")
        print("="*60)
        for index_name, script_name in indexos_a_importar:
            print(f"  • {script_name} (per a l'índex {index_name})")
        print()
        
        # Executar automàticament sense demanar confirmació
        print("Executant automàticament els scripts necessaris...\n")
        
        # Executar scripts
        print("\n" + "="*60)
        print("INICIANT INGESTA...")
        print("="*60)
        
        for index_name, script_name in indexos_a_importar:
            if executar_script(script_name):
                exitosos += 1
            else:
                fallits += 1
                # Continuem automàticament amb els altres scripts encara que hi hagi errors
                print("\n⚠ Error detectat, però continuant amb els altres scripts...")
    else:
        print("="*60)
        print("✓ TOTS ELS ÍNDEXS TENEN DADES SUFICIENTS")
        print("="*60)
        print("\nNo cal executar cap script d'ingesta.")
    
    # Sempre verificar si cal marcar Pokémon prohibits (independentment de si s'han importat índexs)
    pokemon_count = comptar_documents("pokemon")
    if pokemon_count > 0:
        print("\n" + "="*60)
        print("VERIFICANT MARCADO DE POKÉMON PROHIBITS...")
        print("="*60)
        
        # Verificar si hi ha Pokémon sense el camp is_banned
        try:
            response = requests.get(f"{ELASTIC_URL}/pokemon/_search", json={
                "query": {
                    "bool": {
                        "must_not": {
                            "exists": {"field": "is_banned"}
                        }
                    }
                },
                "size": 1
            })
            
            # També verificar si hi ha Pokémon prohibits marcats
            response_prohibits = requests.get(f"{ELASTIC_URL}/pokemon/_search", json={
                "query": {
                    "term": {"is_banned": True}
                },
                "size": 1
            })
            
            pokemon_sense_marcar = response.json()['hits']['total']['value']
            pokemon_prohibits = response_prohibits.json()['hits']['total']['value']
            
            # Si no hi ha cap Pokémon prohibit marcat i hi ha molts Pokémon, cal executar el script
            if pokemon_prohibits == 0 and pokemon_count >= 100:
                print(f"Detectat: {pokemon_count} Pokémon però cap prohibit marcat.")
                print("Executant script per marcar Pokémon prohibits...\n")
                
                if executar_script("marcar_pokemon_prohibits.py"):
                    exitosos += 1
                    print("✓ Pokémon prohibits marcats correctament")
                else:
                    fallits += 1
                    print("⚠ Error al marcar Pokémon prohibits")
            elif pokemon_sense_marcar > 0:
                print(f"Detectat: {pokemon_sense_marcar} Pokémon sense camp is_banned.")
                print("Executant script per marcar Pokémon prohibits...\n")
                
                if executar_script("marcar_pokemon_prohibits.py"):
                    exitosos += 1
                    print("✓ Pokémon prohibits marcats correctament")
                else:
                    fallits += 1
                    print("⚠ Error al marcar Pokémon prohibits")
            else:
                print(f"✓ Pokémon prohibits ja estan marcats correctament ({pokemon_prohibits} prohibits trobats)")
        except Exception as e:
            print(f"⚠ Error verificant estat de Pokémon prohibits: {e}")
    
    # Resum final
    print("\n" + "="*60)
    print("RESUM FINAL")
    print("="*60)
    print(f"Scripts executats amb èxit: {exitosos}")
    print(f"Scripts fallits: {fallits}")
    print(f"Índexs que ja tenien dades: {len(indexos_ok)}")
    
    # Verificar estat final
    print("\n" + "="*60)
    print("ESTAT FINAL DELS ÍNDEXS:")
    print("="*60)
    for index_name, _ in SCRIPTS_INGESTA.items():
        count = comptar_documents(index_name)
        limit_minim = LIMITS_MINIMS.get(index_name, 0)
        status = "✓" if count >= limit_minim else "⚠"
        print(f"  {status} {index_name:12} : {count:>5} documents")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main()

