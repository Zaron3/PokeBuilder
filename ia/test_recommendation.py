"""
Script de Test per al Sistema de Recomanació
=============================================

Aquest script prova el sistema de recomanació amb diferents escenaris.

Ús:
    python3 test_recommendation.py
"""

import sys
import os

# Afegir el directori actual al path
sys.path.insert(0, os.path.dirname(__file__))

from ai_service import AIService
from recommendation_engine import format_recommendation_text


def print_separator(title=""):
    """Imprimeix un separador visual."""
    if title:
        print(f"\n{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}\n")
    else:
        print(f"{'='*60}\n")


def test_scenario(service, scenario_name, team_ids):
    """
    Prova un escenari específic.
    
    Args:
        service: Instància d'AIService
        scenario_name: Nom de l'escenari
        team_ids: Llista d'IDs de l'equip
    """
    print_separator(f"ESCENARI: {scenario_name}")
    
    # Obtenir noms dels Pokémon
    team = service.get_pokemon_by_ids(team_ids)
    print(f"Equip actual ({len(team)} Pokémon):")
    for p in team:
        types_str = ', '.join(t.capitalize() for t in p.types)
        print(f"  • {p.name.capitalize()} (#{p.pokedex_id}) - {types_str}")
    
    # Analitzar equip
    print("\n📊 Anàlisi de l'equip:")
    analysis = service.analyze_team(team_ids)
    
    print(f"\nTipus presents: {', '.join(t.capitalize() for t in analysis['present_types'])}")
    
    if analysis['weaknesses']:
        weak_list = sorted(analysis['weaknesses'].items(), key=lambda x: x[1], reverse=True)
        print(f"\nDebilitats principals:")
        for wtype, count in weak_list[:5]:
            print(f"  • {wtype.capitalize()}: {count} Pokémon dèbils")
    
    if analysis['resistances']:
        resist_list = sorted(analysis['resistances'].items(), key=lambda x: x[1], reverse=True)
        print(f"\nResistències principals:")
        for rtype, count in resist_list[:5]:
            print(f"  • {rtype.capitalize()}: {count} Pokémon resistents")
    
    # Obtenir recomanacions
    print("\n🎯 Generant recomanacions...")
    recommendations = service.recommend_pokemon(team_ids, top_n=5)
    
    if not recommendations:
        print("No s'han trobat recomanacions.")
        return
    
    print(f"\n✨ Top {len(recommendations)} Recomanacions:\n")
    
    for i, rec in enumerate(recommendations, 1):
        types_str = ', '.join(t.capitalize() for t in rec['types'])
        print(f"{i}. {rec['name'].upper()} (#{rec['pokedex_id']}) - {types_str}")
        print(f"   Puntuació Global: {rec['score']:.1f}/100")
        print(f"   • Defensiva: {rec['scores']['defensive']:.1f}/100")
        print(f"   • Ofensiva: {rec['scores']['offensive']:.1f}/100")
        print(f"   • Diversitat: {rec['scores']['diversity']:.1f}/100")
        print(f"   • Estadístiques: {rec['scores']['stats']:.1f}/100")
        
        print(f"\n   Raons principals:")
        for reason in rec['reasoning'][:3]:
            print(f"   → {reason}")
        print()


def main():
    """Funció principal de test."""
    print_separator("TEST DEL SISTEMA DE RECOMANACIÓ IA")
    
    try:
        # Inicialitzar servei
        print("Inicialitzant servei d'IA...")
        service = AIService()
        print(f"✓ Servei inicialitzat amb {len(service.type_chart)} tipus carregats\n")
        
        # Escenari 1: Equip inicial (starters de Kanto)
        test_scenario(
            service,
            "Equip Inicial - Starters de Kanto",
            [1, 4, 7]  # Bulbasaur, Charmander, Squirtle
        )
        
        # Escenari 2: Equip amb debilitat a Electric
        test_scenario(
            service,
            "Equip amb Debilitat a Electric",
            [7, 130, 144]  # Squirtle, Gyarados, Articuno (tots Water/Flying)
        )
        
        # Escenari 3: Equip equilibrat
        test_scenario(
            service,
            "Equip Equilibrat",
            [25, 94, 143, 248]  # Pikachu, Gengar, Snorlax, Tyranitar
        )
        
        # Escenari 4: Equip d'un sol tipus
        test_scenario(
            service,
            "Equip Mono-Fire",
            [4, 37, 58]  # Charmander, Vulpix, Growlithe
        )
        
        # Escenari 5: Equip gairebé complet
        test_scenario(
            service,
            "Equip Gairebé Complet (5/6)",
            [1, 4, 7, 25, 94]  # Bulbasaur, Charmander, Squirtle, Pikachu, Gengar
        )
        
        print_separator("TESTS COMPLETATS AMB ÈXIT")
        print("✓ Tots els escenaris s'han executat correctament")
        
    except Exception as e:
        print(f"\n✗ Error durant els tests: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
