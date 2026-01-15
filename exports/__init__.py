"""
Module exports - Génération de rapports HTML et Word
"""

from .html_export import generate_html_report
from .word_export import generate_word_report

__all__ = [
    'generate_html_report',
    'generate_word_report',
]