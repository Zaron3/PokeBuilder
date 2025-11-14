"""
Paquet de IA per a PokeBuilder
===============================

Aquest paquet conté el sistema de recomanació intel·ligent per a PokeBuilder.

Mòduls:
    - recommendation_engine: Motor principal de recomanació
    - ai_service: Servei que connecta amb Elasticsearch

Ús:
    from ia.ai_service import AIService
    
    service = AIService()
    recommendations = service.recommend_pokemon([1, 4, 7], top_n=5)
"""

__version__ = "1.0.0"
__author__ = "PokeBuilder Team"

from .recommendation_engine import (
    RecommendationEngine,
    Pokemon,
    TypeEffectiveness,
    Recommendation,
    format_recommendation_text
)

from .ai_service import AIService

__all__ = [
    'RecommendationEngine',
    'Pokemon',
    'TypeEffectiveness',
    'Recommendation',
    'format_recommendation_text',
    'AIService'
]
