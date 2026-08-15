"""
Module utils - Imports centralisés pour l'analyse de données
"""

from .data_loader import load_file
from .data_cleaner import clean_and_preprocess, get_data_quality_score
from .analyzer import analyze_dataframe
from .visualizations import create_visualizations
from .ai_insights import (
    generate_ai_insights,      # API Anthropic
    llm_insights_local,        # Ollama
    generate_basic_insights,   # Basique
    normalize_insights_for_report,
    test_api_key
)
from .local_llm import (
    check_ollama_available,
    list_ollama_models,
    generate_local_insights
)

__all__ = [
    # Data loading
    'load_file',
    
    # Data cleaning
    'clean_and_preprocess',
    'get_data_quality_score',
    
    # Analysis
    'analyze_dataframe',
    
    # Visualizations
    'create_visualizations',
    
    # AI Insights
    'generate_basic_insights',
    'normalize_insights_for_report',
    'llm_insights_local',
    'generate_ai_insights',
    'test_api_key',
    
    # Local LLM (Ollama)
    'check_ollama_available',
    'list_ollama_models',
    'generate_local_insights',
]