"""
Module utils - Imports centralisés pour l'analyse de données
"""

from .data_loader import load_file
from .data_cleaner import clean_and_preprocess, get_data_quality_score
from .analyzer import analyze_dataframe
from .visualizations import create_visualizations
from .ai_insights import (
    generate_ai_insights,      # API Anthropic (principal)
    generate_basic_insights,   # Basique (filet de sécurité)
    normalize_insights_for_report,
    test_api_key
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
    'generate_ai_insights',
    'test_api_key',
]