"""
Application Streamlit - Générateur de Rapports IA
Version commerciale avec authentification
"""

import streamlit as st
import pandas as pd
import io
from datetime import datetime
from typing import Optional, Dict, Any

# ==========================================
# 🔒 AUTHENTIFICATION - DOIT ÊTRE AVANT st.set_page_config()
# ==========================================
from utils.auth_trial import (
    check_login,
    can_generate_report,
    increment_report_count,
    show_quota_sidebar,
    show_upgrade_message,
    logout
)

# Vérifier l'authentification AVANT tout
if not check_login():
    st.stop()  # Bloquer si non authentifié

# ==========================================
# Configuration de la page (APRÈS authentification)
# ==========================================
st.set_page_config(
    page_title="AI Report Generator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Imports des modules (APRÈS st.set_page_config)
from config import CSS_STYLES, t
from utils import (
    load_file,
    clean_and_preprocess,
    get_data_quality_score,
    analyze_dataframe,
    create_visualizations,
)

# ==========================================
# IMPORTS IA - VERSION UNIFIÉE (SIMPLIFIÉE)
# ==========================================
from utils.ai_insights import (
    generate_basic_insights,
    normalize_insights_for_report,
    llm_insights_local,
    generate_ai_insights,
)


# Imports des exports
from exports import generate_html_report, generate_word_report

# ==========================================
# DICTIONNAIRE DE TRADUCTIONS COMPLET
# ==========================================
TRANSLATIONS_FULL = {
    'fr': {
        # Messages de chargement
        'data_loaded': 'Données chargées',
        'data_loaded_warnings': 'Données chargées avec avertissements',
        'quality_issues': 'Problèmes de qualité détectés',
        'lines': 'lignes',
        'columns': 'colonnes',
        'quality': 'Qualité',
        'cleaning_details': 'Détails nettoyage',
        'original': 'Original',
        'cleaned': 'Nettoyé',
        'removed_columns': 'Colonnes supprimées',
        'removed_duplicates': 'Doublons supprimés',
        
        # TAB 1 - Quality
        'empty_columns_removed': 'Colonnes vides supprimées',
        'duplicate_rows_removed': 'Lignes dupliquées supprimées',
        'converted_to_numeric': 'Colonnes converties en numérique',
        'no_cleaning_needed': 'Aucune action de nettoyage nécessaire',
        'why_columns_removed': 'Pourquoi ces colonnes ont été supprimées ?',
        'total_removed': 'colonne(s) supprimée(s)',
        'removal_reasons': 'Raisons de suppression :',
        'completely_empty': 'Colonnes complètement vides (100% de valeurs manquantes)',
        'nearly_empty': 'Colonnes quasi-vides (>95% de valeurs manquantes)',
        'complete_list': 'Liste complète des colonnes supprimées :',
        'info_message': "💡 Ces colonnes n'apportaient aucune information utile à l'analyse. Leur suppression améliore la qualité du rapport et réduit le bruit dans les données.",
        
        # Métriques
        'excellent': 'Excellent',
        'good': 'Bon',
        'needs_improvement': 'À améliorer',
    },
    'en': {
        # Loading messages
        'data_loaded': 'Data loaded',
        'data_loaded_warnings': 'Data loaded with warnings',
        'quality_issues': 'Quality issues detected',
        'lines': 'rows',
        'columns': 'columns',
        'quality': 'Quality',
        'cleaning_details': 'Cleaning details',
        'original': 'Original',
        'cleaned': 'Cleaned',
        'removed_columns': 'Removed columns',
        'removed_duplicates': 'Removed duplicates',
        
        # TAB 1 - Quality
        'empty_columns_removed': 'Empty columns removed',
        'duplicate_rows_removed': 'Duplicate rows removed',
        'converted_to_numeric': 'Columns converted to numeric',
        'no_cleaning_needed': 'No cleaning actions required',
        'why_columns_removed': 'Why were these columns removed?',
        'total_removed': 'column(s) removed',
        'removal_reasons': 'Removal reasons:',
        'completely_empty': 'Completely empty columns (100% missing values)',
        'nearly_empty': 'Nearly empty columns (>95% missing values)',
        'complete_list': 'Complete list of removed columns:',
        'info_message': "💡 These columns provided no useful information for analysis. Their removal improves report quality and reduces data noise.",
        
        # Metrics
        'excellent': 'Excellent',
        'good': 'Good',
        'needs_improvement': 'Needs improvement',
    }
}

def tr(key: str, lang: str = 'fr') -> str:
    """Fonction de traduction rapide"""
    return TRANSLATIONS_FULL.get(lang, TRANSLATIONS_FULL['fr']).get(key, key)


# ==========================================
# INITIALISATION SESSION STATE
# ==========================================
def init_session_state():
    """Initialise toutes les variables de session"""
    defaults = {
        'ui_lang': 'fr',
        'report_lang': 'fr',
        'export_format': 'HTML',
        'df': None,
        'df_original': None,
        'cleaning_report': None,
        'analysis': None,
        'ai_insights': None,
        'visualizations': None,
        '_last_uploaded_name': None,
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def load_any_file(uploaded_file) -> Optional[pd.DataFrame]:
    """Charge n'importe quel type de fichier supporté"""
    if uploaded_file is None:
        return None
    
    try:
        uploaded_file.seek(0)
    except:
        pass
    
    name = uploaded_file.name.lower()
    
    try:
        if name.endswith('.csv'):
            return pd.read_csv(uploaded_file)
        elif name.endswith(('.xlsx', '.xls')):
            return pd.read_excel(uploaded_file)
        elif name.endswith('.json'):
            return pd.read_json(uploaded_file)
        elif name.endswith('.parquet'):
            return pd.read_parquet(uploaded_file)
        else:
            st.error(f"❌ Format non supporté: {name}")
            return None
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement: {str(e)}")
        return None


def reset_analysis_on_new_file(current_name: str):
    """Reset l'analyse si nouveau fichier"""
    if st.session_state._last_uploaded_name != current_name:
        st.session_state.df = None
        st.session_state.df_original = None
        st.session_state.cleaning_report = None
        st.session_state.analysis = None
        st.session_state.ai_insights = None
        st.session_state.visualizations = None
        st.session_state._last_uploaded_name = current_name


def show_home_screen(lang: str):
    """Affiche l'écran d'accueil"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.info(
            "👈 " + (
                "Upload a file in the sidebar to start" 
                if lang == 'en' 
                else "Téléchargez un fichier dans la barre latérale pour commencer"
            )
        )
    
    st.markdown("---")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        if lang == 'fr':
            st.markdown("""
            ### 🚀 Fonctionnalités
            - **📁 Multi-format**: CSV, Excel, JSON, Parquet
            - **🧹 Nettoyage automatique** des données
            - **📊 Analyse statistique** complète
            - **📈 Visualisations interactives** (6 types)
            - **🧠 Insights IA** (3 modes disponibles)
            - **📄 Rapports professionnels** (HTML + Word)
            - **🌍 Interface bilingue** (FR/EN)
            """)
        else:
            st.markdown("""
            ### 🚀 Features
            - **📁 Multi-format**: CSV, Excel, JSON, Parquet
            - **🧹 Automatic data cleaning**
            - **📊 Complete statistical analysis**
            - **📈 Interactive visualizations** (6 types)
            - **🧠 AI insights** (3 modes available)
            - **📄 Professional reports** (HTML + Word)
            - **🌍 Bilingual interface** (FR/EN)
            """)
    
    with col_b:
        if lang == 'fr':
            st.markdown("""
            ### 💼 Cas d'Usage
            - 📈 Analyse de ventes
            - 📊 Rapports marketing
            - 🔍 Études de marché
            - 💰 Analyse financière
            - 🎓 Projets académiques
            - 📉 Business Intelligence
            """)
        else:
            st.markdown("""
            ### 💼 Use Cases
            - 📈 Sales analysis
            - 📊 Marketing reports
            - 🔍 Market research
            - 💰 Financial analysis
            - 🎓 Academic projects
            - 📉 Business Intelligence
            """)


# ==========================================
# INITIALISATION
# ==========================================
init_session_state()

st.markdown(CSS_STYLES, unsafe_allow_html=True)

st.markdown(
    f'<h1 class="main-header">{t("title", st.session_state.ui_lang)}</h1>',
    unsafe_allow_html=True
)

st.markdown(
    f"""
<div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 1rem; border-radius: 10px; text-align: center;
            margin-bottom: 2rem; box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);">
    <p style="color: white; font-size: 1.2rem; font-weight: 600; margin: 0;">
        {t("subtitle", st.session_state.ui_lang)}
    </p>
</div>
""",
    unsafe_allow_html=True,
)


# ==========================================
# SIDEBAR - CONFIGURATION
# ==========================================

with st.sidebar:
    st.header(t("config", st.session_state.ui_lang))
    
    ui_lang = st.selectbox(
        "🌍 Interface Language",
        options=["fr", "en"],
        format_func=lambda x: "🇫🇷 Français" if x == "fr" else "🇬🇧 English",
        index=0 if st.session_state.ui_lang == "fr" else 1,
    )
    
    if st.session_state.ui_lang != ui_lang:
        st.session_state.ui_lang = ui_lang
        st.rerun()
    
    # ==========================================
    # 🎁 AFFICHER QUOTA / ESSAI GRATUIT
    # ==========================================
    show_quota_sidebar()
    
    st.markdown("---")
    
    st.markdown(f"### {t('upload', st.session_state.ui_lang)}")
    uploaded_file = st.file_uploader(
        t("upload_help", st.session_state.ui_lang),
        type=["csv", "xlsx", "xls", "json", "parquet"],
        help="CSV, Excel, JSON, Parquet",
    )
    
    st.markdown("---")
    
    st.markdown(f"### {t('ai_section', st.session_state.ui_lang)}")
    
    # Message promotionnel Anthropic
    if st.session_state.ui_lang == "fr":
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 12px; border-radius: 8px; margin-bottom: 15px;">
            <p style="color: white; margin: 0; font-size: 0.9rem; text-align: center;">
                <strong>💡 Recommandé</strong><br>
                Utilisez <strong>Anthropic API</strong> pour des insights de haute qualité en ~30 secondes<br>
                <span style="font-size: 0.8rem; opacity: 0.9;">
                ~500 rapports avec une clé à 5$ | Très économique !
                </span>
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 12px; border-radius: 8px; margin-bottom: 15px;">
            <p style="color: white; margin: 0; font-size: 0.9rem; text-align: center;">
                <strong>💡 Recommended</strong><br>
                Use <strong>Anthropic API</strong> for high-quality insights in ~30 seconds<br>
                <span style="font-size: 0.8rem; opacity: 0.9;">
                ~500 reports with a $5 key | Very economical!
                </span>
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    ai_mode = st.radio(
        "Mode IA" if st.session_state.ui_lang == "fr" else "AI Mode",
        options=["None", "Ollama (Local)", "Anthropic API"],
        help="Choisissez votre fournisseur d'IA" if st.session_state.ui_lang == "fr" else "Choose your AI provider",
    )
    
    api_key: Optional[str] = None
    selected_model: Optional[str] = None
    
    # ==========================================
    # MODE ANTHROPIC API - VERSION COMMERCIALE
    # ==========================================
    if ai_mode == "Anthropic API":
        # ==========================================
        # MODE IA FORCÉ (VERSION COMMERCIALE)
        # ==========================================
        st.info(
            "🧠 Mode IA : Anthropic Claude (Inclus)" 
            if st.session_state.ui_lang == "fr" 
            else "🧠 AI Mode: Anthropic Claude (Included)"
        )
        ai_mode = "Anthropic API"  # Forcé
    
    # ==========================================   
    else:
        st.info(
            "💡 Mode basique (sans IA)" 
            if st.session_state.ui_lang == "fr" 
            else "💡 Basic mode (no AI)"
        )
        st.caption(
            "Les insights seront générés à partir des statistiques de base uniquement." 
            if st.session_state.ui_lang == "fr"
            else "Insights will be generated from basic statistics only."
        )
    
    st.markdown("---")
    
    st.markdown(f"### {t('language', st.session_state.ui_lang)}")
    st.session_state.report_lang = st.selectbox(
        t("language", st.session_state.ui_lang),
        options=["fr", "en"],
        format_func=lambda x: "🇫🇷 Français" if x == "fr" else "🇬🇧 English",
        index=0 if st.session_state.report_lang == "fr" else 1,
    )
    
    st.markdown(f"### {t('export_format', st.session_state.ui_lang)}")
    st.session_state.export_format = st.selectbox(
        t("export_format", st.session_state.ui_lang),
        options=["HTML", "Word"],
        help="HTML: Imprimable en PDF | Word: Éditable .docx",
    )
    # ==========================================
    # 🚪 BOUTON DÉCONNEXION
    # ==========================================
    st.markdown("---")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        user_email = st.session_state.get("user_email", "")
        if user_email:
            st.caption(f"👤 {user_email}")
    
    with col2:
        if st.button("🚪", help="Déconnexion", use_container_width=True):
            logout()

# ==========================================
# MAIN - TRAITEMENT DES DONNÉES
# ==========================================

if uploaded_file is None:
    show_home_screen(st.session_state.ui_lang)
    st.stop()

reset_analysis_on_new_file(uploaded_file.name)

# Charger et nettoyer les données (une seule fois)
if st.session_state.df is None:
    with st.spinner(
        "Chargement et nettoyage des données..." 
        if st.session_state.ui_lang == "fr" 
        else "Loading and cleaning data..."
    ):
        try:
            df_raw = load_any_file(uploaded_file)
            if df_raw is None:
                st.stop()
            
            st.session_state.df_original = df_raw.copy()
            
            # Nettoyer avec la langue UI
            df_cleaned, cleaning_report = clean_and_preprocess(df_raw, st.session_state.ui_lang)
            st.session_state.df = df_cleaned
            st.session_state.cleaning_report = cleaning_report
            
            st.session_state.analysis = analyze_dataframe(df_cleaned)
            
            quality_score = get_data_quality_score(cleaning_report)
            
            # Afficher le résultat (TRADUIT)
            col1, col2 = st.columns([3, 1])
            
            with col1:
                lang = st.session_state.ui_lang
                if quality_score >= 80:
                    st.success(
                        f"✅ {tr('data_loaded', lang)}: {len(df_cleaned):,} {tr('lines', lang)}, "
                        f"{len(df_cleaned.columns)} {tr('columns', lang)} | "
                        f"{tr('quality', lang)}: {quality_score:.0f}/100"
                    )
                elif quality_score >= 60:
                    st.warning(
                        f"⚠️ {tr('data_loaded_warnings', lang)}: {len(df_cleaned):,} {tr('lines', lang)}, "
                        f"{len(df_cleaned.columns)} {tr('columns', lang)} | "
                        f"{tr('quality', lang)}: {quality_score:.0f}/100"
                    )
                else:
                    st.error(
                        f"❌ {tr('quality_issues', lang)}: {len(df_cleaned):,} {tr('lines', lang)}, "
                        f"{len(df_cleaned.columns)} {tr('columns', lang)} | "
                        f"{tr('quality', lang)}: {quality_score:.0f}/100"
                    )
            
            with col2:
                with st.expander(f"🔍 {tr('cleaning_details', lang)}"):
                    orig = cleaning_report.get("original_shape", (0, 0))
                    cleaned = cleaning_report.get("cleaned_shape", (0, 0))
                    st.write(f"**{tr('original', lang)}:** {orig[0]} × {orig[1]}")
                    st.write(f"**{tr('cleaned', lang)}:** {cleaned[0]} × {cleaned[1]}")
                    
                    dropped_cols = cleaning_report.get("dropped_empty_columns", [])
                    if dropped_cols:
                        st.write(f"**{tr('removed_columns', lang)}:** {len(dropped_cols)}")
                    
                    dropped_rows = cleaning_report.get("dropped_duplicate_rows", 0)
                    if dropped_rows:
                        st.write(f"**{tr('removed_duplicates', lang)}:** {dropped_rows}")
        
        except Exception as e:
            st.error(f"❌ Erreur: {str(e)}")
            st.stop()

df = st.session_state.df
analysis = st.session_state.analysis
cleaning_report = st.session_state.cleaning_report

if df is None or analysis is None:
    st.stop()


# ==========================================
# TABS - INTERFACE PRINCIPALE
# ==========================================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🧹 " + ("Qualité" if st.session_state.ui_lang == "fr" else "Quality"),
    "👀 " + ("Vue d'ensemble" if st.session_state.ui_lang == "fr" else "Overview"),
    "📊 " + ("Visualisations" if st.session_state.ui_lang == "fr" else "Visualizations"),
    "🧠 " + ("Insights" if st.session_state.ui_lang == "fr" else "Insights"),
    "📄 " + ("Rapport" if st.session_state.ui_lang == "fr" else "Report"),
])


# ==========================================
# TAB 1: QUALITÉ DES DONNÉES (TRADUIT)
# ==========================================
with tab1:
    lang = st.session_state.ui_lang
    
    st.header(
        "Rapport de Qualité des Données" 
        if lang == "fr" 
        else "Data Quality Report"
    )
    
    quality_score = get_data_quality_score(cleaning_report)
    
    orig = cleaning_report.get("original_shape", (0, 0))
    cleaned = cleaning_report.get("cleaned_shape", (0, 0))
    removed_rows = max(int(orig[0]) - int(cleaned[0]), 0)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        delta_text = tr('excellent', lang) if quality_score >= 80 else tr('good', lang) if quality_score >= 60 else tr('needs_improvement', lang)
        st.metric(
            label="Score Qualité" if lang == "fr" else "Quality Score",
            value=f"{quality_score:.0f}/100",
            delta=delta_text
        )
    
    with col2:
        st.metric(
            label="Lignes Originales" if lang == "fr" else "Original Rows",
            value=f"{int(orig[0]):,}"
        )
    
    with col3:
        st.metric(
            label="Lignes Finales" if lang == "fr" else "Final Rows",
            value=f"{int(cleaned[0]):,}",
            delta=f"-{removed_rows}" if removed_rows > 0 else None
        )
    
    with col4:
        st.metric(
            label="Colonnes" if lang == "fr" else "Columns",
            value=f"{int(cleaned[1])}"
        )
    
    st.markdown("---")
    
    # Actions de nettoyage (TRADUITES)
    #st.subheader(
        #"🔧 Actions de Nettoyage" 
        #if lang == "fr" 
        #else "🔧 Cleaning Actions"
    #)
    
    dropped_cols = cleaning_report.get("dropped_empty_columns", [])
    if dropped_cols:
        st.warning(f"🗑️ {tr('empty_columns_removed', lang)}: {', '.join(map(str, dropped_cols[:5]))}")
        
        # Expander détaillé (TRADUIT)
        if quality_score < 80:
            with st.expander(f"📋 {tr('why_columns_removed', lang)}"):
                st.write(f"**Total : {len(dropped_cols)} {tr('total_removed', lang)}**")
                st.write("")
                st.write(f"**{tr('removal_reasons', lang)}**")
                st.write(f"• {tr('completely_empty', lang)}")
                st.write(f"• {tr('nearly_empty', lang)}")
                st.write("")
                st.write(f"**{tr('complete_list', lang)}**")
                for i, col in enumerate(dropped_cols, 1):
                    st.write(f"{i}. `{col}`")
                st.write("")
                st.info(tr('info_message', lang))
    
    dropped_rows = cleaning_report.get("dropped_duplicate_rows", 0)
    if dropped_rows > 0:
        st.warning(f"🔄 {tr('duplicate_rows_removed', lang)}: {dropped_rows}")
    
    converted = cleaning_report.get("converted_to_numeric", [])
    if converted:
        st.success(f"🔢 {tr('converted_to_numeric', lang)}: {', '.join(map(str, converted[:5]))}")
    
    # ✅ MESSAGE SUPPRIMÉ : "Aucune action nécessaire" était inapproprié
    # Car il ne vérifiait pas les anomalies détectées (colonnes vides, doublons, etc.)
    # Les anomalies sont maintenant affichées dans leur propre section ci-dessous
    
    # ==========================================
    # ✅ NOUVEAU : RAPPORT DÉTAILLÉ DES ANOMALIES
    # ==========================================
    from utils.data_cleaner import get_detailed_anomaly_report
    
    anomaly_report = get_detailed_anomaly_report(cleaning_report, st.session_state.ui_lang)
    
    if anomaly_report['summary']['total_anomalies'] > 0:
        st.markdown("---")
        st.subheader(
            "⚠️ Anomalies Détectées" 
            if st.session_state.ui_lang == "fr" 
            else "⚠️ Detected Anomalies"
        )
        
        # Colonnes complètement vides
        if anomaly_report['empty_columns']['count'] > 0:
            with st.expander(
                f"📭 {anomaly_report['empty_columns']['count']} Colonne(s) Complètement Vide(s)" 
                if st.session_state.ui_lang == "fr"
                else f"📭 {anomaly_report['empty_columns']['count']} Completely Empty Column(s)",
                expanded=False
            ):
                cols_str = ", ".join(anomaly_report['empty_columns']['columns'])
                st.write(cols_str)
                st.caption(
                    "Ces colonnes ne contiennent aucune donnée et seront exclues des visualisations."
                    if st.session_state.ui_lang == "fr"
                    else "These columns contain no data and will be excluded from visualizations."
                )
        
        # Colonnes quasi-vides (≥90%)
        if anomaly_report['quasi_empty_columns']['count'] > 0:
            with st.expander(
                f"⚠️ {anomaly_report['quasi_empty_columns']['count']} Colonne(s) Quasi-Vides (≥90%)" 
                if st.session_state.ui_lang == "fr"
                else f"⚠️ {anomaly_report['quasi_empty_columns']['count']} Quasi-Empty Column(s) (≥90%)",
                expanded=False
            ):
                cols_str = ", ".join(anomaly_report['quasi_empty_columns']['columns'])
                st.write(cols_str)
                st.caption(
                    "Ces colonnes ont ≥90% de valeurs manquantes et seront exclues des visualisations."
                    if st.session_state.ui_lang == "fr"
                    else "These columns have ≥90% missing values and will be excluded from visualizations."
                )
        
        # Doublons
        if anomaly_report['duplicates']['count'] > 0:
            st.warning(
                f"🔄 {anomaly_report['duplicates']['count']:,} ligne(s) dupliquée(s) ({anomaly_report['duplicates']['percentage']:.1f}%)"
                if st.session_state.ui_lang == "fr"
                else f"🔄 {anomaly_report['duplicates']['count']:,} duplicate row(s) ({anomaly_report['duplicates']['percentage']:.1f}%)"
            )
        
        # Valeurs manquantes importantes (>50%)
        if anomaly_report['high_missing_values']:
            with st.expander(
                f"📊 {len(anomaly_report['high_missing_values'])} Colonne(s) avec >50% de Valeurs Manquantes"
                if st.session_state.ui_lang == "fr"
                else f"📊 {len(anomaly_report['high_missing_values'])} Column(s) with >50% Missing Values",
                expanded=False
            ):
                for item in anomaly_report['high_missing_values']:
                    st.write(f"• **{item['column']}**: {item['percentage']:.1f}%")
    
    
    st.markdown("---")
    
    # Valeurs manquantes
    st.subheader(
        "📊 Valeurs Manquantes" 
        if lang == "fr" 
        else "📊 Missing Values"
    )
    
    missing_after = cleaning_report.get("missing_values_after", {})
    if missing_after:
        miss_df = pd.DataFrame([
            {"Colonne" if lang == "fr" else "Column": k, 
             "Manquants" if lang == "fr" else "Missing": int(v)}
            for k, v in missing_after.items()
        ]).sort_values(
            "Manquants" if lang == "fr" else "Missing", 
            ascending=False
        ).head(20)
        
        st.dataframe(miss_df, use_container_width=True, height=400)
    else:
        st.info(
            "✅ Aucune valeur manquante détectée" 
            if lang == "fr" 
            else "✅ No missing values detected"
        )


# ==========================================
# TAB 2: VUE D'ENSEMBLE
# ==========================================
with tab2:
    st.header(
        "Vue d'Ensemble" 
        if st.session_state.ui_lang == "fr" 
        else "Overview"
    )
    
    col1, col2, col3, col4 = st.columns(4)
    
    stats_cards = [
        ("OBSERVATIONS", analysis["shape"][0]),
        ("VARIABLES", analysis["shape"][1]),
        ("NUMÉRIQUES" if st.session_state.ui_lang == "fr" else "NUMERIC", 
         len(analysis.get("numeric_cols", []))),
        ("CATÉGORIELLES" if st.session_state.ui_lang == "fr" else "CATEGORICAL", 
         len(analysis.get("categorical_cols", [])))
    ]
    
    for col, (label, value) in zip([col1, col2, col3, col4], stats_cards):
        with col:
            st.markdown(
                f"""
                <div class="stat-card">
                    <h3 style="font-size: 0.9rem; margin-bottom: 0.5rem;">{label}</h3>
                    <p style="font-size: 2.5rem; font-weight: 800; margin: 0;">{value:,}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
    
    st.markdown("---")
    
    st.subheader(
        "📋 Aperçu des Données" 
        if st.session_state.ui_lang == "fr" 
        else "📋 Data Preview"
    )
    st.dataframe(df.head(20), use_container_width=True, height=400)
    
    if analysis.get("numeric_summary"):
        st.markdown("---")
        st.subheader(
            "📈 Statistiques Descriptives" 
            if st.session_state.ui_lang == "fr" 
            else "📈 Descriptive Statistics"
        )
        
        stats_df = pd.DataFrame(analysis["numeric_summary"]).T
        st.dataframe(stats_df, use_container_width=True)
    
    if analysis.get("categorical_summary"):
        st.markdown("---")
        st.subheader(
            "🏷️ Distribution des Catégories" 
            if st.session_state.ui_lang == "fr" 
            else "🏷️ Category Distribution"
        )
        
        for col_name, info in list(analysis.get("categorical_summary", {}).items())[:5]:
            with st.expander(f"📌 {col_name}"):
                top_values = info.get("top_values", [])
                if top_values:
                    dist_df = pd.DataFrame(
                        top_values,
                        columns=[
                            "Catégorie" if st.session_state.ui_lang == "fr" else "Category",
                            "Nombre" if st.session_state.ui_lang == "fr" else "Count"
                        ]
                    )
                    st.dataframe(dist_df, use_container_width=True)


# ==========================================
# TAB 3: VISUALISATIONS
# ==========================================
with tab3:
    st.header(
        "Visualisations" 
        if st.session_state.ui_lang == "fr" 
        else "Visualizations"
    )
    
    # Générer les visualisations (une seule fois)
    if st.session_state.visualizations is None:
        with st.spinner(
            "Génération des graphiques..." 
            if st.session_state.ui_lang == "fr" 
            else "Generating charts..."
        ):
            # ✅ NOUVEAU : Obtenir les colonnes à exclure (vides + quasi-vides ≥90%)
            from utils.data_cleaner import get_columns_to_exclude_from_viz
            exclude_cols = get_columns_to_exclude_from_viz(cleaning_report)
            
            # ✅ MODIFIÉ : Passer exclude_cols aux visualisations
            st.session_state.visualizations = create_visualizations(
                df, 
                st.session_state.report_lang,
                exclude_cols=exclude_cols  # ← NOUVEAU PARAMÈTRE
            )
            
    visualizations = st.session_state.visualizations
    
    if not visualizations:
        st.warning(
            "⚠️ Aucune visualisation disponible" 
            if st.session_state.ui_lang == "fr" 
            else "⚠️ No visualizations available"
        )
    else:
        for viz_name, (fig, interpretation) in visualizations.items():
            viz_title = viz_name.replace('_', ' ').title()
            
            st.subheader(viz_title)
            st.pyplot(fig, use_container_width=True)
            
            if interpretation:
                st.markdown(
                    f'<div class="insight-box">💡 {interpretation}</div>',
                    unsafe_allow_html=True
                )
            
            st.markdown("---")


# ==========================================
# TAB 4: INSIGHTS IA
# ==========================================
with tab4:
    st.header(
        "Insights IA" 
        if st.session_state.ui_lang == "fr" 
        else "AI Insights"
    )
    
    colA, colB = st.columns([3, 1])
    
    with colA:
        # ==========================================
        # MODE ANTHROPIC API
        # ==========================================
        if ai_mode == "Anthropic API" and api_key:
            # Importer les fonctions
            from utils.ai_insights import generate_ai_insights
            from utils.data_cleaner import get_detailed_anomaly_report
                        
            # ✅ NOUVEAU : Obtenir le rapport d'anomalies
            anomaly_report = get_detailed_anomaly_report(
                cleaning_report, 
                st.session_state.report_lang
            )
                        
            # ✅ NOUVEAU : Ajouter au contexte d'analyse
            analysis['anomaly_report'] = anomaly_report
                        
            st.session_state.ai_insights = generate_ai_insights(
                analysis, 
                api_key, 
                lang=st.session_state.report_lang
            )
        elif ai_mode == "Anthropic API" and not api_key:
                st.warning(
                    "⚠️ Clé API requise pour le mode Anthropic" 
                    if st.session_state.ui_lang == "fr"
                    else "⚠️ API key required for Anthropic mode"
                )
        # ==========================================
        # MODE OLLAMA LOCAL
        # ==========================================
        elif ai_mode == "Ollama (Local)" and selected_model:
                        # ... warnings ...
                        
            from utils.ai_insights import llm_insights_local, normalize_insights_for_report
            from utils.data_cleaner import get_detailed_anomaly_report
                        
            # ✅ NOUVEAU : Obtenir le rapport d'anomalies
            anomaly_report = get_detailed_anomaly_report(
                cleaning_report, 
                st.session_state.report_lang
            )
                        
            # ✅ NOUVEAU : Ajouter au contexte
            analysis['anomaly_report'] = anomaly_report
                        
            # Générer avec Ollama
            raw_insights = llm_insights_local(
                df,
                analysis,
                lang=st.session_state.report_lang,
                model=selected_model
            )
        elif ai_mode == "Ollama (Local)" and not selected_model:
                st.warning(
                    "⚠️ Sélectionnez un modèle dans la barre latérale" 
                    if st.session_state.ui_lang == "fr"
                    else "⚠️ Select a model in the sidebar"
                )
        else:
            st.info("💡 Mode basique (sans IA)"
                if st.session_state.ui_lang == "fr"
                else "💡 Basic mode (no AI)"
            )
                
    
    with colB:
        can_generate = True
        if ai_mode == "Anthropic API" and not api_key:
            can_generate = False
        elif ai_mode == "Ollama (Local)" and not selected_model:
            can_generate = False
        
        if st.button(
            "🚀 Générer" if st.session_state.ui_lang == "fr" else "🚀 Generate",
            type="primary",
            use_container_width=True,
            disabled=not can_generate
        ):
            # ==========================================
            # ✅ VÉRIFIER QUOTA AVANT GÉNÉRATION
            # ==========================================
            can_generate_report_bool, quota_message = can_generate_report()
            
            if not can_generate_report_bool:
                # Quota épuisé
                show_upgrade_message()
                st.stop()
            
            # Afficher message si essai gratuit
            if quota_message:
                st.info(f"💡 {quota_message}")
            
            with st.spinner(
                "🧠 Analyse en cours..." 
                if st.session_state.ui_lang == "fr" 
                else "🧠 Analyzing..."
            ):
                try:
                    if ai_mode == "Anthropic API" and api_key:
                        st.session_state.ai_insights = generate_ai_insights(
                            analysis, 
                            api_key, 
                            lang=st.session_state.report_lang
                        )
                    
                    elif ai_mode == "Ollama (Local)" and selected_model:
                        if any(x in selected_model.lower() for x in ['7b', '8b', 'latest']):
                            if not any(x in selected_model.lower() for x in ['1b', '3b']):
                                st.warning(
                                    f"⏳ Le modèle {selected_model} peut être lent (3-5 min). Soyez patient !" 
                                    if st.session_state.ui_lang == "fr"
                                    else f"⏳ Model {selected_model} may be slow (3-5 min). Be patient!"
                                )
                        
                        raw_insights = llm_insights_local(
                            df,
                            analysis,
                            lang=st.session_state.report_lang,
                            model=selected_model
                        )
                        
                        st.session_state.ai_insights = normalize_insights_for_report(raw_insights)
                    
                    else:
                        st.session_state.ai_insights = generate_basic_insights(
                            analysis,
                            lang=st.session_state.report_lang
                        )
                    
                    st.success(
                        "✅ Insights générés !" 
                        if st.session_state.ui_lang == "fr" 
                        else "✅ Insights generated!"
                    )
                    
                    # ==========================================
                    # ✅ INCRÉMENTER LE COMPTEUR DE RAPPORTS
                    # ==========================================
                    increment_report_count()
                    
                    # Afficher quota restant
                    from utils.auth_trial import get_quota_info
                    quota = get_quota_info()
                    if quota["is_trial"]:
                        st.info(f"🎁 Essai gratuit : {quota['remaining']} rapport(s) restant(s)")
                    
                    st.rerun()
                
                except Exception as e:
                    st.error(f"❌ Claude API: {str(e)}")

                    error_str = str(e).lower()
                    
                    if "timeout" in error_str:
                        st.info(
                            "💡 Le modèle prend du temps. Réessayez ou utilisez llama3.2:3b" 
                            if st.session_state.ui_lang == "fr"
                            else "💡 Model is slow. Retry or use llama3.2:3b"
                        )
                    elif "json" in error_str:
                        st.info(
                            "💡 Réponse invalide du modèle. Essayez llama3.2:3b" 
                            if st.session_state.ui_lang == "fr"
                            else "💡 Invalid model response. Try llama3.2:3b"
                        )
                    elif "api key" in error_str or "401" in error_str:
                        st.info(
                            "💡 Vérifiez votre clé API sur console.anthropic.com" 
                            if st.session_state.ui_lang == "fr"
                            else "💡 Check your API key at console.anthropic.com"
                        )
    
    # Affichage des insights
    if st.session_state.ai_insights:
        insights = st.session_state.ai_insights
        
        st.markdown(
            f"""
            <div class="insight-box">
                <h3>{'Résumé exécutif' if st.session_state.report_lang == 'fr' else 'Executive summary'}</h3>
                <p>{insights.get('resume_executif','')}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        
        st.subheader(
            "Tendances principales" 
            if st.session_state.report_lang == "fr" 
            else "Key findings"
        )
        for i, trend in enumerate(insights.get("tendances_principales", []) or [], 1):
            st.info(f"**{i}.** {trend}")
        
        if insights.get("insights"):
            st.subheader(
                "Analyse approfondie" 
                if st.session_state.report_lang == "fr" 
                else "Deep analysis"
            )
            for item in insights["insights"]:
                title = item.get("titre", "Insight")
                desc = item.get("description", "")
                with st.expander(f"🔍 {title}"):
                    st.write(desc)
        
        if insights.get("anomalies"):
            st.subheader(
                "Anomalies" 
                if st.session_state.report_lang == "fr" 
                else "Anomalies"
            )
            for a in insights["anomalies"]:
                if a and a.lower() not in ['none', 'aucune', 'no']:
                    st.warning(a)
        
        st.subheader(
            "Recommandations" 
            if st.session_state.report_lang == "fr" 
            else "Recommendations"
        )
        for i, rec in enumerate(insights.get("recommandations", []) or [], 1):
            if isinstance(rec, dict):
                action = rec.get('action', '')
                justif = rec.get('justification', '')
                st.success(f"**{i}. {action}**\n\n_{justif}_")
            else:
                st.success(f"**{i}. {rec}**")
        
        st.subheader("Conclusion")
        st.markdown(f"_{insights.get('conclusion','')}_")


# ==========================================
# TAB 5: RAPPORT FINAL
# ==========================================
with tab5:
    st.header(
        "Rapport Final" 
        if st.session_state.ui_lang == "fr" 
        else "Final Report"
    )
    
    if not st.session_state.ai_insights:
        st.warning(
            "⚠️ Veuillez d'abord générer les insights dans l'onglet 'Insights'" 
            if st.session_state.ui_lang == "fr" 
            else "⚠️ Please generate insights first in the 'Insights' tab"
        )
    else:
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.info(
                f"📄 **Format**: {st.session_state.export_format} | "
                f"🌍 **Langue**: {'Français' if st.session_state.report_lang == 'fr' else 'English'}"
            )
            
            st.markdown("---")
            
            with st.spinner(
                "Génération de l'aperçu..." 
                if st.session_state.ui_lang == "fr" 
                else "Generating preview..."
            ):
                report_html = generate_html_report(
                    df,
                    analysis,
                    st.session_state.ai_insights,
                    lang=st.session_state.report_lang,
                    visualizations=st.session_state.visualizations
                )
            
            st.subheader(
                "👁️ Aperçu du Rapport HTML" 
                if st.session_state.ui_lang == "fr" 
                else "👁️ HTML Report Preview"
            )
            
            st.components.v1.html(report_html, height=700, scrolling=True)
            
            st.markdown("---")
            
            st.subheader(
                "⬇️ Télécharger le Rapport" 
                if st.session_state.ui_lang == "fr" 
                else "⬇️ Download Report"
            )
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                st.download_button(
                    label="📄 HTML" + (" (Pour PDF)" if st.session_state.ui_lang == "fr" else " (For PDF)"),
                    data=report_html.encode('utf-8'),
                    file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
                    mime="text/html",
                    use_container_width=True,
                    help="Ouvrez dans un navigateur puis Ctrl+P pour sauvegarder en PDF"
                )
            
            with col_b:
                if st.button(
                    "📝 Word (.docx)",
                    use_container_width=True,
                    help="Rapport éditable au format Word"
                ):
                    with st.spinner(
                        "Génération du rapport Word..." 
                        if st.session_state.ui_lang == "fr" 
                        else "Generating Word report..."
                    ):
                        try:
                            word_bytes = generate_word_report(
                                df,
                                analysis,
                                st.session_state.ai_insights,
                                lang=st.session_state.report_lang,
                                visualizations=st.session_state.visualizations
                            )
                            
                            st.download_button(
                                label="⬇️ Télécharger Word" if st.session_state.ui_lang == "fr" else "⬇️ Download Word",
                                data=word_bytes,
                                file_name=f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                use_container_width=True,
                            )
                            
                            st.success(
                                "✅ Rapport Word généré !" 
                                if st.session_state.ui_lang == "fr" 
                                else "✅ Word report generated!"
                            )
                        
                        except Exception as e:
                            st.error(f"❌ Erreur: {str(e)}")
            
            st.markdown("---")
            
            with st.expander(
                "💡 Conseils d'utilisation" 
                if st.session_state.ui_lang == "fr" 
                else "💡 Usage Tips"
            ):
                if st.session_state.ui_lang == "fr":
                    st.markdown("""
                    **Pour le format HTML:**
                    1. Téléchargez le fichier HTML
                    2. Ouvrez-le dans votre navigateur (Chrome, Firefox, Edge)
                    3. Appuyez sur `Ctrl+P` (ou `Cmd+P` sur Mac)
                    4. Sélectionnez "Enregistrer en PDF"
                    5. Vous obtenez un PDF professionnel avec tous les graphiques
                    
                    **Pour le format Word:**
                    1. Téléchargez le fichier .docx
                    2. Ouvrez-le dans Word, Google Docs ou LibreOffice
                    3. Personnalisez le contenu, les styles, etc.
                    4. Exportez en PDF si nécessaire
                    
                    **Avantages de chaque format:**
                    - **HTML → PDF**: Mise en page parfaite, couleurs préservées, idéal pour partage
                    - **Word**: Éditable, personnalisable, idéal pour collaboration
                    """)
                else:
                    st.markdown("""
                    **For HTML format:**
                    1. Download the HTML file
                    2. Open it in your browser (Chrome, Firefox, Edge)
                    3. Press `Ctrl+P` (or `Cmd+P` on Mac)
                    4. Select "Save as PDF"
                    5. You get a professional PDF with all graphics
                    
                    **For Word format:**
                    1. Download the .docx file
                    2. Open it in Word, Google Docs or LibreOffice
                    3. Customize content, styles, etc.
                    4. Export to PDF if needed
                    
                    **Advantages of each format:**
                    - **HTML → PDF**: Perfect layout, preserved colors, ideal for sharing
                    - **Word**: Editable, customizable, ideal for collaboration
                    """)


# ==========================================
# FOOTER
# ==========================================
st.markdown("---")
st.markdown(
    """
    <div style="text-align: center; color: #6b7280; font-size: 0.9rem; padding: 2rem 0;">
        <p><strong>Générateur de Rapports </strong> | Développé avec ❤️</p>
        <p style="font-size: 0.8rem; margin-top: 0.5rem;">
            Propulsé par Streamlit & Claude AI | © 2025
        </p>
    </div>
    <div style="text-align: center; color: #6b7280; font-size: 0.9rem; padding: 2rem 0;">
        <p><strong> Report Generator </strong> | Developed with ❤️</p> 
    <p style="font-size: 0.8rem; margin-top: 0.5rem;">
            Propulsed by Streamlit & Claude AI | © 2025
        </p>
    </div>
    """,
    
    unsafe_allow_html=True,
)
