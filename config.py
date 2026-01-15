"""
Configuration et traductions pour l'application
"""

# Traductions FR/EN
TRANSLATIONS = {
    'fr': {
        'title': 'Générateur de Rapports IA',
        'subtitle': 'Analyse augmentée par Intelligence Artificielle',
        'config': '⚙️ Configuration',
        'upload': 'Charger les données',
        'upload_help': 'Formats supportés',
        'ai_section': '🔑 Intelligence Artificielle',
        'api_key': 'Clé API Anthropic (optionnel)',
        'api_help': 'Pour des insights IA avancés. Laissez vide pour analyse basique.',
        'ai_active': '✅ Mode IA activé',
        'basic_mode': '💡 Mode analyse basique',
        'language': '🌍 Langue du rapport',
        'export_format': '📄 Format d\'export',
        'tab_overview': '📊 Vue d\'ensemble',
        'tab_viz': '📈 Visualisations',
        'tab_insights': '🧠 Insights',
        'tab_report': '📄 Rapport',
        'observations': 'Observations',
        'variables': 'Variables',
        'numeric': 'Numériques',
        'categorical': 'Catégorielles',
        'generate_insights': '🚀 Générer les Insights',
        'generate_report': '📥 Générer le Rapport',
        'download': '⬇️ Télécharger',
        'executive_summary': 'Résumé Exécutif',
        'main_trends': 'Tendances Principales',
        'deep_analysis': 'Analyses Approfondies',
        'anomalies': 'Anomalies',
        'recommendations': 'Recommandations Stratégiques',
        'conclusion': 'Conclusion',
        'report_title': 'RAPPORT D\'ANALYSE PROFESSIONNEL',
        'overview': 'VUE D\'ENSEMBLE',
        'detailed_stats': 'STATISTIQUES DÉTAILLÉES',
        'insights_ai': 'INSIGHTS IA',
        'data_preview': 'Aperçu des données',
        'descriptive_stats': 'Statistiques descriptives',
        'category_dist': 'Distribution des catégories',
    },
    'en': {
        'title': 'AI Report Generator',
        'subtitle': 'AI-Powered Data Analysis',
        'config': '⚙️ Configuration',
        'upload': 'Load Data',
        'upload_help': 'Supported formats',
        'ai_section': '🔑 Artificial Intelligence',
        'api_key': 'Anthropic API Key (optional)',
        'api_help': 'For advanced AI insights. Leave empty for basic analysis.',
        'ai_active': '✅ AI Mode Enabled',
        'basic_mode': '💡 Basic Analysis Mode',
        'language': '🌍 Report Language',
        'export_format': '📄 Export Format',
        'tab_overview': '📊 Overview',
        'tab_viz': '📈 Visualizations',
        'tab_insights': '🧠 Insights',
        'tab_report': '📄 Report',
        'observations': 'Observations',
        'variables': 'Variables',
        'numeric': 'Numeric',
        'categorical': 'Categorical',
        'generate_insights': '🚀 Generate Insights',
        'generate_report': '📥 Generate Report',
        'download': '⬇️ Download',
        'executive_summary': 'Executive Summary',
        'main_trends': 'Main Trends',
        'deep_analysis': 'Deep Analysis',
        'anomalies': 'Anomalies',
        'recommendations': 'Strategic Recommendations',
        'conclusion': 'Conclusion',
        'report_title': 'PROFESSIONAL ANALYSIS REPORT',
        'overview': 'OVERVIEW',
        'detailed_stats': 'DETAILED STATISTICS',
        'insights_ai': 'AI INSIGHTS',
        'data_preview': 'Data Preview',
        'descriptive_stats': 'Descriptive Statistics',
        'category_dist': 'Category Distribution',
    }
}

def t(key, lang='fr'):
    """Fonction de traduction"""
    return TRANSLATIONS.get(lang, TRANSLATIONS['fr']).get(key, key)

# Styles CSS pour Streamlit
CSS_STYLES = """
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem;
    }
    .stat-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
    }
    .insight-box {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border-left: 4px solid #667eea;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
"""

# Configuration des couleurs pour les graphiques
COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d']