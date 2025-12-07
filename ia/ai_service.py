"""
Servei d'IA per a PokeBuilder
==============================

Aquest mòdul proporciona la interfície entre el motor de recomanació
i la base de dades Elasticsearch.

Autor: PokeBuilder Team
Data: Novembre 2024
"""

from typing import List, Dict, Optional
from elasticsearch import Elasticsearch
from recommendation_engine import (
    RecommendationEngine,
    Pokemon,
    TypeEffectiveness,
    Recommendation,
    format_recommendation_text
)


class AIService:
    """
    Servei que gestiona les recomanacions d'IA connectant-se a Elasticsearch.
    """

    def __init__(self, es_host: str = "http://localhost:9200"):
        """
        Inicialitza el servei d'IA.
        
        Args:
            es_host: URL del servidor Elasticsearch
        """
        self.es = Elasticsearch(hosts=[es_host], verify_certs=False)
        self.type_chart = {}
        self.engine = None

        # Carregar dades de tipus
        self._load_type_chart()

        # Inicialitzar motor de recomanació
        self.engine = RecommendationEngine(self.type_chart)

    def _load_type_chart(self):
        """
        Carrega la informació de tipus des d'Elasticsearch.
        """
        try:
            # Obtenir tots els tipus
            response = self.es.search(
                index="types",
                body={
                    "query": {"match_all": {}},
                    "size": 100
                }
            )

            for hit in response['hits']['hits']:
                type_data = hit['_source']
                self.type_chart[type_data['name']] = TypeEffectiveness(
                    name=type_data['name'],
                    double_damage_from=type_data.get('double_damage_from', []),
                    half_damage_from=type_data.get('half_damage_from', []),
                    no_damage_from=type_data.get('no_damage_from', []),
                    double_damage_to=type_data.get('double_damage_to', []),
                    half_damage_to=type_data.get('half_damage_to', []),
                    no_damage_to=type_data.get('no_damage_to', [])
                )

            print(f"✓ Carregats {len(self.type_chart)} tipus")

        except Exception as e:
            print(f"✗ Error carregant tipus: {e}")
            raise

    def get_pokemon_by_ids(self, pokedex_ids: List[int]) -> List[Pokemon]:
        """
        Obté Pokémon per IDs des d'Elasticsearch.
        (Versió optimitzada amb consulta 'terms')
        
        Args:
            pokedex_ids: Llista d'IDs de Pokédex
            
        Returns:
            Llista de Pokémon
        """
        if not pokedex_ids:
            return []

        pokemon_map = {}
        pokemon_list = []

        try:
            response = self.es.search(
                index="pokemon",
                body={
                    "query": {
                        "terms": {"pokedex_id": pokedex_ids}
                    },
                    "size": len(pokedex_ids)
                }
            )

            for hit in response['hits']['hits']:
                data = hit['_source']
                pokemon = Pokemon(
                    pokedex_id=data['pokedex_id'],
                    name=data['name'],
                    types=data['types'],
                    stats=data['stats']
                )
                pokemon_map[data['pokedex_id']] = pokemon

            # Reconstruir la llista en l'ordre original sol·licitat
            for pid in pokedex_ids:
                if pid in pokemon_map:
                    pokemon_list.append(pokemon_map[pid])
                else:
                    print(f"Avís: No s'ha trobat Pokémon amb ID {pid} a Elasticsearch")

        except Exception as e:
            print(f"Error obtenint Pokémon per IDs {pokedex_ids}: {e}")

        return pokemon_list

    def get_all_pokemon(self, limit: int = 1000, exclude_banned: bool = True) -> List[Pokemon]:
        """
        Obté tots els Pokémon disponibles.
        
        Args:
            limit: Nombre màxim de Pokémon a retornar
            
        Returns:
            Llista de tots els Pokémon
        """
        try:
            query = {"match_all": {}}

            if exclude_banned:
                query = {
                    "term": {
                        "is_banned": False
                    }
                }

            response = self.es.search(
                index="pokemon",
                body={
                    "query": query,
                    "size": limit
                }
            )

            pokemon_list = []
            for hit in response['hits']['hits']:
                data = hit['_source']
                pokemon_list.append(Pokemon(
                    pokedex_id=data['pokedex_id'],
                    name=data['name'],
                    types=data['types'],
                    stats=data['stats']
                ))

            return pokemon_list

        except Exception as e:
            print(f"Error obtenint tots els Pokémon: {e}")
            return []

    def recommend_pokemon(
            self,
            team_ids: List[int],
            top_n: int = 5
    ) -> List[Dict]:
        """
        Genera recomanacions de Pokémon per a un equip.
        
        Args:
            team_ids: Llista d'IDs dels Pokémon actuals a l'equip
            top_n: Nombre de recomanacions a retornar
            
        Returns:
            Llista de diccionaris amb recomanacions
        """
        # Obtenir Pokémon de l'equip actual
        current_team = self.get_pokemon_by_ids(team_ids)

        if len(current_team) >= 6:
            return []

        # Obtenir tots els Pokémon disponibles
        all_pokemon = self.get_all_pokemon(exclude_banned=True)

        # Generar recomanacions
        recommendations = self.engine.recommend(current_team, all_pokemon, top_n)

        # Convertir a format de diccionari per a l'API
        result = []
        for rec in recommendations:
            result.append({
                "pokedex_id": rec.pokemon.pokedex_id,
                "name": rec.pokemon.name,
                "types": rec.pokemon.types,
                "sprite_url": f"https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/{rec.pokemon.pokedex_id}.png",
                "stats": rec.pokemon.stats,
                "score": round(rec.score, 2),
                "scores": {
                    "defensive": round(rec.defensive_score, 2),
                    "offensive": round(rec.offensive_score, 2),
                    "diversity": round(rec.diversity_score, 2),
                    "stats": round(rec.stats_score, 2)
                },
                "reasoning": rec.reasoning,
                "warnings": rec.warnings, # (NOVETAT) Afegit camp d'avisos
                "explanation": format_recommendation_text(rec)
            })

        return result

    def analyze_team(self, team_ids: List[int]) -> Dict:
        """
        Analitza un equip i retorna les seves fortaleses i debilitats.
        
        Args:
            team_ids: Llista d'IDs dels Pokémon de l'equip
            
        Returns:
            Diccionari amb l'anàlisi de l'equip
        """
        current_team = self.get_pokemon_by_ids(team_ids)

        if not current_team:
            return {
                "team_size": 0,
                "weaknesses": {},
                "resistances": {},
                "immunities": [],
                "type_coverage": [],
                "avg_stats": {}
            }

        # Utilitzar el mètode d'anàlisi del motor
        analysis = self.engine._analyze_team(current_team)

        return {
            "team_size": len(current_team),
            "weaknesses": analysis['weaknesses'],
            "resistances": analysis['resistances'],
            "immunities": list(analysis['immunities']),
            "type_coverage": list(analysis['offensive_types']),
            "avg_stats": analysis['avg_stats'],
            "present_types": list(analysis['present_types'])
        }

    def get_team_vulnerability(self, team_ids: List[int]) -> Dict:
        """
        Analitza un equip i retorna la seva vulnerabilitat màxima de tipus.

        Args:
            team_ids: Llista d'IDs dels Pokémon de l'equip

        Returns:
            Diccionari amb l'anàlisi de vulnerabilitat.
        """
        current_team = self.get_pokemon_by_ids(team_ids)

        if not current_team:
            return {
                "most_vulnerable_type": "N/A",
                "max_multiplier": 0.0,
                "is_balanced": True,
                "vulnerability_details": {}
            }

        # Utilitzar el mètode d'anàlisi de vulnerabilitat del motor
        vulnerability_analysis = self.engine.get_team_vulnerability(current_team)

        return vulnerability_analysis


# Funció auxiliar per a testing
def test_ai_service():
    """
    Funció de test per verificar el funcionament del servei.
    """
    print("=== Test del Servei d'IA ===\n")

    try:
        # Inicialitzar servei
        print("1. Inicialitzant servei...")
        service = AIService()
        print("   ✓ Servei inicialitzat\n")

        # Test amb un equip d'exemple
        print("2. Provant recomanacions amb equip d'exemple...")
        team_ids = [1, 4, 7]  # Bulbasaur, Charmander, Squirtle

        print(f"   Equip actual: {team_ids}")

        # Analitzar equip
        print("\n3. Analitzant equip...")
        analysis = service.analyze_team(team_ids)
        print(f"   Tipus presents: {analysis['present_types']}")
        print(f"   Debilitats principals: {list(analysis['weaknesses'].keys())[:5]}")

        # Obtenir recomanacions
        print("\n4. Generant recomanacions...")
        recommendations = service.recommend_pokemon(team_ids, top_n=3)

        print(f"\n   Top {len(recommendations)} recomanacions:")
        for i, rec in enumerate(recommendations, 1):
            print(f"\n   {i}. {rec['name'].capitalize()} (#{rec['pokedex_id']})")
            print(f"      Puntuació: {rec['score']}/100")
            print(f"      Raons principals (PROS):")
            for reason in rec['reasoning'][:3]:
                print(f"      • {reason}")

            if rec['warnings']:
                print(f"      Avisos (CONTRES):")
                for warning in rec['warnings']:
                    print(f"      • {warning}")

        print("\n✓ Test completat amb èxit!")
        return True

    except Exception as e:
        print(f"\n✗ Error durant el test: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_ai_service()