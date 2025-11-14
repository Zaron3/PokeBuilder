"""
Sistema de Recomanació IA per a PokeBuilder
============================================

Aquest mòdul implementa un sistema de recomanació intel·ligent que analitza
l'equip actual de l'usuari i suggereix Pokémon que complementin l'equip
basant-se en diversos criteris:

1. Cobertura defensiva (debilitats de tipus)
2. Cobertura ofensiva (diversitat d'atac)
3. Diversitat de tipus
4. Equilibri d'estadístiques

Autor: PokeBuilder Team
Data: Novembre 2024
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import math


@dataclass
class Pokemon:
    """Representa un Pokémon amb les seves característiques."""
    pokedex_id: int
    name: str
    types: List[str]
    stats: Dict[str, int]


@dataclass
class TypeEffectiveness:
    """Representa l'efectivitat d'un tipus contra altres tipus."""
    name: str
    double_damage_from: List[str]  # Dèbil contra
    half_damage_from: List[str]    # Resistent a
    no_damage_from: List[str]      # Immune a
    double_damage_to: List[str]    # Efectiu contra
    half_damage_to: List[str]      # Poc efectiu contra
    no_damage_to: List[str]        # No fa dany a


@dataclass
class Recommendation:
    """Representa una recomanació de Pokémon amb la seva puntuació i raonament."""
    pokemon: Pokemon
    score: float
    defensive_score: float
    offensive_score: float
    diversity_score: float
    stats_score: float
    reasoning: List[str] # PROS
    warnings: List[str]  # CONTRES


class RecommendationEngine:
    """
    Motor de recomanació que analitza equips i suggereix Pokémon.
    """
    
    # Pesos per al càlcul de la puntuació final
    WEIGHTS = {
        'defensive': 0.30,
        'offensive': 0.20,
        'diversity': 0.20,
        'stats': 0.30
    }
    
    def __init__(self, type_chart: Dict[str, TypeEffectiveness]):
        """
        Inicialitza el motor de recomanació.
        
        Args:
            type_chart: Diccionari amb informació d'efectivitat de tipus
        """
        self.type_chart = type_chart
        self.all_type_names = list(self.type_chart.keys())
    
    def recommend(
        self,
        current_team: List[Pokemon],
        all_pokemon: List[Pokemon],
        top_n: int = 5
    ) -> List[Recommendation]:
        """
        Genera recomanacions de Pokémon per complementar l'equip actual.
        
        Args:
            current_team: Llista de Pokémon actuals a l'equip (màxim 5)
            all_pokemon: Llista de tots els Pokémon disponibles
            top_n: Nombre de recomanacions a retornar
            
        Returns:
            Llista de recomanacions ordenades per puntuació
        """
        if len(current_team) >= 6:
            return []
        
        # Analitzar l'equip actual
        team_analysis = self._analyze_team(current_team)
        
        # Calcular puntuacions per a tots els candidats
        recommendations = []
        for pokemon in all_pokemon:
            # Saltar Pokémon ja presents a l'equip
            if any(p.pokedex_id == pokemon.pokedex_id for p in current_team):
                continue
            
            rec = self._evaluate_candidate(pokemon, current_team, team_analysis)
            recommendations.append(rec)
        
        # Ordenar per puntuació i retornar top N
        recommendations.sort(key=lambda x: x.score, reverse=True)
        return recommendations[:top_n]
    
    def _analyze_team(self, team: List[Pokemon]) -> Dict:
        """
        Analitza l'equip actual per identificar fortaleses i debilitats.
        
        Returns:
            Diccionari amb l'anàlisi de l'equip
        """
        analysis = {
            'weaknesses': {},      # Tipus contra els quals l'equip és dèbil (net)
            'resistances': {},     # Tipus als quals l'equip resisteix (total)
            'immunities': set(),   # Tipus als quals l'equip és immune
            'offensive_types': set(),  # Tipus que l'equip colpeja com a súper-efectiu
            'present_types': set(),    # Tipus defensius presents a l'equip
            'avg_stats': {},       # Estadístiques mitjanes
            'total_members': len(team)
        }
        
        if not team:
            return analysis
        
        # Analitzar debilitats i resistències
        all_weaknesses = {}
        all_resistances = {}
        
        for pokemon in team:
            for poke_type in pokemon.types:
                analysis['present_types'].add(poke_type)
                
                if poke_type in self.type_chart:
                    type_data = self.type_chart[poke_type]
                    
                    for weak_type in type_data.double_damage_from:
                        all_weaknesses[weak_type] = all_weaknesses.get(weak_type, 0) + 1
                    
                    for resist_type in type_data.half_damage_from:
                        all_resistances[resist_type] = all_resistances.get(resist_type, 0) + 1
                    
                    for immune_type in type_data.no_damage_from:
                        analysis['immunities'].add(immune_type)
                    
                    for effective_type in type_data.double_damage_to:
                        analysis['offensive_types'].add(effective_type)
        
        # Determinar les debilitats netes de l'equip
        team_weaknesses = {}
        
        for type_name, weak_count in all_weaknesses.items():
            resist_count = all_resistances.get(type_name, 0)
            
            if type_name in analysis['immunities']:
                continue
            
            if weak_count > resist_count:
                team_weaknesses[type_name] = weak_count - resist_count
        
        analysis['weaknesses'] = team_weaknesses
        analysis['resistances'] = all_resistances
        
        # Calcular estadístiques mitjanes
        stat_names = ['hp', 'attack', 'defense', 'special_attack', 'special_defense', 'speed']
        for stat in stat_names:
            total = sum(p.stats.get(stat, 0) for p in team)
            analysis['avg_stats'][stat] = total / len(team) if team else 0
        
        return analysis

    # ======================================================================
    # ============= NOVA FUNCIÓ D'EFECTIVITAT NETA =========================
    # ======================================================================
    def _calculate_net_effectiveness(self, candidate_types: List[str]) -> Dict[str, set]:
        """
        Calcula el perfil defensiu net (debilitats, resistències, immunitats)
        d'un conjunt de tipus (un Pokémon).
        
        Args:
            candidate_types: Llista de tipus del Pokémon (ex: ['steel', 'rock'])
            
        Returns:
            Diccionari amb "weaknesses", "resistances", "immunities" netes.
        """
        net_defense = {
            "weaknesses": set(),
            "resistances": set(),
            "immunities": set()
        }

        # Iterar per tots els 18 tipus com a "tipus atacant"
        for attacking_type in self.all_type_names:
            current_multiplier = 1.0
            
            # Comprovar l'efecte de l'atacant contra cada tipus defensiu
            for defense_type_name in candidate_types:
                if defense_type_name not in self.type_chart:
                    continue
                
                # Obtenim el perfil del tipus defensiu
                defense_type_data = self.type_chart[defense_type_name]
                
                # Comprovem com li afecta el 'attacking_type'
                if attacking_type in defense_type_data.double_damage_from:
                    current_multiplier *= 2
                elif attacking_type in defense_type_data.half_damage_from:
                    current_multiplier *= 0.5
                elif attacking_type in defense_type_data.no_damage_from:
                    current_multiplier = 0
                    break # És immune, el multiplicador final és 0
            
            # Classificar el multiplicador final
            if current_multiplier == 0:
                net_defense["immunities"].add(attacking_type)
            elif current_multiplier > 1: # Inclou x2 i x4
                net_defense["weaknesses"].add(attacking_type)
            elif current_multiplier < 1: # Inclou x0.5 i x0.25
                net_defense["resistances"].add(attacking_type)
            # Si current_multiplier == 1, és neutre i no s'afegeix enlloc
        
        return net_defense
    # ======================================================================
    # ======================================================================

    
    def _evaluate_candidate(
        self,
        candidate: Pokemon,
        team: List[Pokemon],
        team_analysis: Dict
    ) -> Recommendation:
        """
        Avalua un candidat i calcula la seva puntuació.
        
        Returns:
            Objecte Recommendation amb puntuació i raonament
        """
        all_reasons = []
        all_warnings = []
        
        # 1. Puntuació defensiva
        defensive_score, def_reasons, def_warnings = self._calculate_defensive_score(
            candidate, team_analysis
        )
        all_reasons.extend(def_reasons)
        all_warnings.extend(def_warnings)
        
        # 2. Puntuació ofensiva
        offensive_score, off_reasons, off_warnings = self._calculate_offensive_score(
            candidate, team_analysis
        )
        all_reasons.extend(off_reasons)
        all_warnings.extend(off_warnings)
        
        # 3. Puntuació de diversitat
        diversity_score, div_reasons, div_warnings = self._calculate_diversity_score(
            candidate, team_analysis
        )
        all_reasons.extend(div_reasons)
        all_warnings.extend(div_warnings)
        
        # 4. Puntuació d'estadístiques
        stats_score, stat_reasons, stat_warnings = self._calculate_stats_score(
            candidate, team_analysis
        )
        all_reasons.extend(stat_reasons)
        all_warnings.extend(stat_warnings)
        
        # Calcular puntuació final
        final_score = (
            defensive_score * self.WEIGHTS['defensive'] +
            offensive_score * self.WEIGHTS['offensive'] +
            diversity_score * self.WEIGHTS['diversity'] +
            stats_score * self.WEIGHTS['stats']
        )
        
        return Recommendation(
            pokemon=candidate,
            score=final_score,
            defensive_score=defensive_score,
            offensive_score=offensive_score,
            diversity_score=diversity_score,
            stats_score=stats_score,
            reasoning=all_reasons,
            warnings=all_warnings
        )
    
    # ======================================================================
    # ========= _calculate_defensive_score REFACTORITZAT ===================
    # ======================================================================
    def _calculate_defensive_score(
        self,
        candidate: Pokemon,
        team_analysis: Dict
    ) -> Tuple[float, List[str], List[str]]:
        """
        Calcula la puntuació defensiva basada en el perfil defensiu NET.
        Aquesta versió és més robusta i evita contradiccions.
        
        Returns:
            Tupla (puntuació, raons, avisos)
        """
        score = 50.0
        reasons = set()
        warnings = set()
        
        team_weaknesses = team_analysis['weaknesses']
        team_immunities = team_analysis['immunities']
        
        # 1. Obtenir el perfil defensiu NET del candidat
        candidate_net_defense = self._calculate_net_effectiveness(candidate.types)
        
        # 2. PROS: Comprovar si les resistències/immunitats del candidat
        #    cobreixen les debilitats de l'equip.
        for resist_type in candidate_net_defense["resistances"]:
            if resist_type in team_weaknesses:
                bonus = team_weaknesses[resist_type] * 10
                score += bonus
                reasons.add(f"Resisteix {resist_type.capitalize()}, una debilitat de l'equip")
        
        for immune_type in candidate_net_defense["immunities"]:
            if immune_type in team_weaknesses:
                bonus = team_weaknesses[immune_type] * 15
                score += bonus
                reasons.add(f"És immune a {immune_type.capitalize()}, una debilitat crítica")
        
        # 3. CONTRES: Comprovar si les debilitats NETES del candidat
        #    creen nous problemes o n'apilen d'existents.
        for weak_type in candidate_net_defense["weaknesses"]:
            if weak_type in team_immunities:
                continue # Un altre membre de l'equip és immune, no penalitzar

            if weak_type in team_weaknesses:
                # Penalització per APILAR debilitats
                penalty = team_weaknesses[weak_type] * 7 
                score -= penalty
                warnings.add(f"Comparteix debilitat a {weak_type.capitalize()}")
            else:
                # Penalització per AFEGIR debilitat NOVA
                penalty = 5 
                score -= penalty
                warnings.add(f"Afegeix una nova debilitat a {weak_type.capitalize()}")
        
        # Normalitzar a 0-100
        score = max(0, min(100, score))
        
        return score, list(reasons), list(warnings)
    # ======================================================================
    # ======================================================================


    def _calculate_offensive_score(
        self,
        candidate: Pokemon,
        team_analysis: Dict
    ) -> Tuple[float, List[str], List[str]]:
        """
        Calcula la puntuació ofensiva.
        
        Returns:
            Tupla (puntuació, raons, avisos)
        """
        score = 50.0
        reasons = []
        warnings = []
        
        # Tipus que l'equip JA colpeja com a súper-efectiu
        team_offensive_coverage = team_analysis['offensive_types']
        
        # Tipus que el candidat pot colpejar que l'equip NO podia
        candidate_new_coverage = set()
        
        for poke_type in candidate.types:
            if poke_type not in self.type_chart:
                continue
            
            type_data = self.type_chart[poke_type]
            
            for effective_type in type_data.double_damage_to:
                if effective_type not in team_offensive_coverage:
                    candidate_new_coverage.add(effective_type)
        
        if candidate_new_coverage:
            # Bonificació per cada nou tipus que pot colpejar
            bonus = len(candidate_new_coverage) * 5
            score += bonus
            reasons.append(
                f"Cobreix ofensivament tipus nous: {', '.join(t.capitalize() for t in candidate_new_coverage)}"
            )
        else:
            score -= 10
            warnings.append("No afegeix nova cobertura ofensiva súper-efectiva")
        
        # Normalitzar a 0-100
        score = max(0, min(100, score))
        
        return score, reasons, warnings
    
    def _calculate_diversity_score(
        self,
        candidate: Pokemon,
        team_analysis: Dict
    ) -> Tuple[float, List[str], List[str]]:
        """
        Calcula la puntuació de diversitat.
        
        Returns:
            Tupla (puntuació, raons, avisos)
        """
        score = 50.0
        reasons = []
        warnings = []
        
        # Tipus defensius ja presents a l'equip
        present_types = team_analysis['present_types']
        
        # Bonificació per tipus nous
        new_types = [t for t in candidate.types if t not in present_types]
        
        if len(new_types) == 2:
            score += 30
            reasons.append(
                f"Afegeix dos tipus defensius nous: {' i '.join(t.capitalize() for t in new_types)}"
            )
        elif len(new_types) == 1:
            score += 20
            reasons.append(f"Afegeix tipus defensiu nou: {new_types[0].capitalize()}")
        else:
            score -= 10
            warnings.append("Tipus defensius ja presents a l'equip")
        
        # Bonificació per doble tipus (més versatilitat defensiva)
        if len(candidate.types) == 2:
            score += 10
            reasons.append("Doble tipus proporciona versatilitat defensiva")
        
        # Normalitzar a 0-100
        score = max(0, min(100, score))
        
        return score, reasons, warnings
    
    def _calculate_stats_score(
        self,
        candidate: Pokemon,
        team_analysis: Dict
    ) -> Tuple[float, List[str], List[str]]:
        """
        Calcula la puntuació d'estadístiques.
        
        Returns:
            Tupla (puntuació, raons, avisos)
        """
        avg_stats = team_analysis['avg_stats']
        
        if not avg_stats or not any(avg_stats.values()):
            return 50.0, [], [] # Equip buit, puntuació neutral
        
        score = 50.0
        reasons = []
        
        stat_names_cat = {
            'hp': 'HP',
            'attack': 'Atac',
            'defense': 'Defensa',
            'special_attack': 'Atac Especial',
            'special_defense': 'Defensa Especial',
            'speed': 'Velocitat'
        }

        # 1. Compensar estadístiques baixes (comparant amb la mitjana)
        low_stats = []
        for stat, avg in avg_stats.items():
            if avg < 80: # Llindar genèric per "baix"
                low_stats.append(stat)
        
        for stat in low_stats:
            candidate_stat = candidate.stats.get(stat, 0)
            team_avg = avg_stats.get(stat, 0)
            
            # Bonificació si el candidat és significativament millor que la mitjana
            if candidate_stat > team_avg + 15:
                bonus = (candidate_stat - team_avg) / 10 # Bonus dinàmic
                score += bonus
                reasons.append(f"Millora {stat_names_cat[stat]} ({candidate_stat}) respecte la mitjana ({team_avg:.0f})")

        # 2. Balanç Ofensiu (Físic/Especial)
        avg_atk = avg_stats.get('attack', 0)
        avg_sp_atk = avg_stats.get('special_attack', 0)
        cand_atk = candidate.stats.get('attack', 0)
        cand_sp_atk = candidate.stats.get('special_attack', 0)

        # Si l'equip és molt físic, bonificar atacants especials
        if avg_atk > avg_sp_atk + 15 and cand_sp_atk > cand_atk + 15:
            score += 10
            reasons.append("Equilibra l'equip afegint un atacant especial")
        # Si l'equip és molt especial, bonificar atacants físics
        elif avg_sp_atk > avg_atk + 15 and cand_atk > cand_sp_atk + 15:
            score += 10
            reasons.append("Equilibra l'equip afegint un atacant físic")

        # 3. Balanç Defensiu (Físic/Especial)
        avg_def = avg_stats.get('defense', 0)
        avg_sp_def = avg_stats.get('special_defense', 0)
        cand_def = candidate.stats.get('defense', 0)
        cand_sp_def = candidate.stats.get('special_defense', 0)

        if avg_def > avg_sp_def + 15 and cand_sp_def > cand_def + 10:
            score += 7
            reasons.append("Equilibra les defenses amb més defensa especial")
        elif avg_sp_def > avg_def + 15 and cand_def > cand_sp_def + 10:
            score += 7
            reasons.append("Equilibra les defenses amb més defensa física")

        # 4. Bonificació general per stats altes
        total_stats = sum(candidate.stats.values())
        if total_stats > 520:
            score += 5
            reasons.append(f"Estadístiques base totals altes ({total_stats})")
        
        # Normalitzar a 0-100
        score = max(0, min(100, score))
        
        return score, reasons, [] # No hi ha avisos per estadístiques


def format_recommendation_text(rec: Recommendation) -> str:
    """
    Formata una recomanació en text llegible.
    (Versió actualitzada amb secció d'Avisos)
    
    Args:
        rec: Objecte Recommendation
        
    Returns:
        Text formatat amb la recomanació
    """
    lines = [
        f"**{rec.pokemon.name.capitalize()}** (#{rec.pokemon.pokedex_id})",
        f"Tipus: {', '.join(t.capitalize() for t in rec.pokemon.types)}",
        f"Puntuació: {rec.score:.1f}/100",
        "",
        "**Per què aquest Pokémon?**"
    ]
    
    # Mostrar un màxim de 4 raons principals per claredat
    main_reasons = rec.reasoning[:4]
    
    if not main_reasons:
        lines.append("• Aporta un equilibri general a l'equip.")
    else:
        for reason in main_reasons:
            lines.append(f"• {reason}")
    
    # (NOVETAT) Afegir secció d'avisos (contres) si n'hi ha
    if rec.warnings:
        lines.append("")
        lines.append("**⚠️ Compte amb...**")
        for warning in rec.warnings:
            lines.append(f"• {warning}")

    lines.extend([
        "",
        "**Detall de puntuacions:**",
        f"• Defensiva: {rec.defensive_score:.1f}/100",
        f"• Ofensiva: {rec.offensive_score:.1f}/100",
        f"• Diversitat: {rec.diversity_score:.1f}/100",
        f"• Estadístiques: {rec.stats_score:.1f}/100"
    ])
    
    return "\n".join(lines)