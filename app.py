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
# 🔒 AUTHENTIFICATION 
# ==========================================
from utils.auth_supabase import (
    check_login,
    can_generate_report,
    increment_report_count,
    show_quota_sidebar,
    show_upgrade_message,
    handle_password_recovery,
    logout
)
from utils.stripe_checkout import handle_checkout_return, show_upgrade_button, show_manage_subscription_button

# Langue par défaut AVANT tout affichage (connexion, reset mot de passe inclus)
if "ui_lang" not in st.session_state:
    st.session_state.ui_lang = "en"

# Gérer un éventuel lien de réinitialisation de mot de passe AVANT tout,
# même si l'utilisateur n'est pas connecté.
if handle_password_recovery():
    st.stop()

# Vérifier l'authentification AVANT tout
if not check_login():
    st.stop()  # Bloquer si non authentifié

# Traiter un éventuel retour de paiement Stripe (?checkout=success&session_id=...)
handle_checkout_return()

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
# IMPORTS IA - VERSION UNIFIÉE 
# ==========================================
from utils.ai_insights import (
    generate_basic_insights,
    normalize_insights_for_report,
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
        'ui_lang': 'en',
        'report_lang': 'en',
        'export_format': 'HTML',
        'df': None,
        'df_original': None,
        'cleaning_report': None,
        'analysis': None,
        'ai_insights': None,
        'visualizations': None,
        '_last_uploaded_name': None,
        'active_tab': 'quality',
        'chat_history': [],
        'featured_charts': None,
        '_featured_for': None,
        '_use_example_file': False,
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
        st.session_state.chat_history = []
        st.session_state.featured_charts = None
        st.session_state._featured_for = None
        st.session_state.active_tab = "quality"
        st.session_state._last_uploaded_name = current_name


def show_home_screen(lang: str):
    """Affiche l'écran d'accueil"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.info(
            "👈 " + (
                "Upload a file in the sidebar to start (or try the sample dataset also available there)" 
                if lang == 'en' 
                else "Téléchargez un fichier dans la barre latérale pour commencer (ou essayez le jeu de données d'exemple, disponible au même endroit)"
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
            - **🧠 Insights IA** propulsés par Claude (Anthropic)
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
            - **🧠 AI insights** powered by Claude (Anthropic)
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

    if st.session_state.get("show_upgrade_success"):
        st.success(
            "🎉 Bienvenue dans le plan Pro ! Votre quota a été mis à jour."
            if st.session_state.ui_lang == "fr"
            else "🎉 Welcome to the Pro plan! Your quota has been updated."
        )
        st.session_state["show_upgrade_success"] = False

    show_upgrade_button()
    show_manage_subscription_button()

    st.markdown("---")
    
    st.markdown(f"### {t('upload', st.session_state.ui_lang)}")
    uploaded_file = st.file_uploader(
        t("upload_help", st.session_state.ui_lang),
        type=["csv", "xlsx", "xls", "json", "parquet"],
        help="CSV, Excel, JSON, Parquet",
    )

    st.caption(
        "Pas de fichier sous la main ?" if st.session_state.ui_lang == "fr"
        else "Don't have a file handy?"
    )
    if st.button(
        "🎯 Essayer avec un exemple" if st.session_state.ui_lang == "fr" else "🎯 Try with an example",
        use_container_width=True,
    ):
        st.session_state["_use_example_file"] = True
        st.rerun()

    # Un vrai upload prend toujours le dessus sur le mode exemple
    if uploaded_file is not None:
        st.session_state["_use_example_file"] = False
    
    st.markdown("---")
    
    st.markdown(f"### {t('ai_section', st.session_state.ui_lang)}")
    
    # Message promotionnel Anthropic
    if st.session_state.ui_lang == "fr":
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 12px; border-radius: 8px; margin-bottom: 15px;">
            <p style="color: white; margin: 0; font-size: 0.9rem; text-align: center;">
                <strong>💡 Recommandé</strong><br>
                Utilisez <strong>Anthropic API</strong> pour des insights de haute qualité <br>
            </p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 12px; border-radius: 8px; margin-bottom: 15px;">
            <p style="color: white; margin: 0; font-size: 0.9rem; text-align: center;">
                <strong>💡 Recommended</strong><br>
                Use <strong>Anthropic API</strong> for high-quality insights <br> 
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # ==========================================
    # SERVICE IA - ANTHROPIC (PRÉ-CONFIGURÉ)
    # ==========================================
    st.info(
        "🧠 Service IA Claude (Anthropic) - Inclus dans votre plan" 
        if st.session_state.ui_lang == "fr" 
        else "🧠 Claude AI Service (Anthropic) - Included in your plan"
    )
    
    # ✅ CLÉ API PRÉ-CONFIGURÉE (Cachée à l'utilisateur)
    api_key = st.secrets.get("anthropic", {}).get("api_key", "")
    
    if api_key:
        st.success(
            "✅ Service IA activé et prêt" 
            if st.session_state.ui_lang == "fr" 
            else "✅ AI service enabled and ready"
        )
    else:
        st.error(
            "❌ Service IA non configuré. Contactez l'administrateur." 
            if st.session_state.ui_lang == "fr" 
            else "❌ AI service not configured. Contact administrator."
        )
        api_key = None
    
    st.markdown("---")
    
    st.markdown(f"### {t('language', st.session_state.ui_lang)}")
    st.session_state.report_lang = st.selectbox(
        t("language", st.session_state.ui_lang),
        options=["fr", "en"],
        format_func=lambda x: "🇫🇷 Français" if x == "fr" else "🇬🇧 English",
        index=0 if st.session_state.report_lang == "fr" else 1,
    )
    
    st.markdown(f"### {t('export_format', st.session_state.ui_lang)}")
    from utils.plans_config import get_plan as _get_plan_export
    _allowed_formats = [
        f for f in _get_plan_export(st.session_state.get("user_plan", "trial"))["export_formats"]
        if f in ("HTML", "Word")  # PDF = impression du HTML, pas un format de génération séparé
    ]
    if not _allowed_formats:
        _allowed_formats = ["HTML"]

    st.session_state.export_format = st.selectbox(
        t("export_format", st.session_state.ui_lang),
        options=_allowed_formats,
        help="HTML: Imprimable en PDF | Word: Éditable .docx",
    )
    if len(_allowed_formats) == 1 and st.session_state.get("user_plan", "trial") == "trial":
        st.caption(
            "🔒 Export Word disponible avec le plan Pro."
            if st.session_state.ui_lang == "fr"
            else "🔒 Word export available with the Pro plan."
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

if st.session_state.get("_use_example_file"):
    from utils.sample_data import get_example_file
    uploaded_file = get_example_file(st.session_state.ui_lang)
    st.info(
        "🎯 Vous explorez un jeu de données d'exemple (ventes trimestrielles). Uploadez votre propre fichier à tout moment pour repartir sur vos données."
        if st.session_state.ui_lang == "fr"
        else "🎯 You're exploring a sample dataset (quarterly sales). Upload your own file anytime to switch to your data."
    )

if uploaded_file is None:
    show_home_screen(st.session_state.ui_lang)
    st.stop()

reset_analysis_on_new_file(uploaded_file.name)

# ==========================================
# 🔒 LIMITES DE PLAN — taille de fichier
# (pas de vérification pour le dataset d'exemple, toujours dans les clous)
# ==========================================
from utils.plans_config import get_plan
_current_plan = get_plan(st.session_state.get("user_plan", "trial"))
_is_example = st.session_state.get("_use_example_file", False)

if not _is_example and st.session_state.df is None:
    _max_mb = _current_plan.get("max_file_size_mb", -1)
    if _max_mb != -1:
        _file_size_mb = getattr(uploaded_file, "size", 0) / (1024 * 1024)
        if _file_size_mb > _max_mb:
            st.error(
                f"🚫 Fichier trop volumineux ({_file_size_mb:.1f} MB) pour votre plan {_current_plan['name']} (limite: {_max_mb} MB)."
                if st.session_state.ui_lang == "fr"
                else f"🚫 File too large ({_file_size_mb:.1f} MB) for your {_current_plan['name']} plan (limit: {_max_mb} MB)."
            )
            show_upgrade_message()
            st.stop()

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

            # ==========================================
            # 🔒 LIMITES DE PLAN — nombre de lignes
            # (vérifié après chargement, on ne connaît le nombre de lignes qu'ici)
            # ==========================================
            if not _is_example:
                _max_rows = _current_plan.get("max_rows", -1)
                if _max_rows != -1 and len(df_raw) > _max_rows:
                    st.error(
                        f"🚫 Fichier trop volumineux ({len(df_raw):,} lignes) pour votre plan {_current_plan['name']} (limite: {_max_rows:,} lignes)."
                        if st.session_state.ui_lang == "fr"
                        else f"🚫 File has too many rows ({len(df_raw):,}) for your {_current_plan['name']} plan (limit: {_max_rows:,} rows)."
                    )
                    show_upgrade_message()
                    st.session_state._last_uploaded_name = None  # permet de réessayer avec un autre fichier
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
# NAVIGATION - INTERFACE PRINCIPALE
# ==========================================
# ⚠️ On n'utilise PAS st.tabs() : Streamlit ne garantit pas de conserver
# l'onglet actif face à un rerun (même déclenché par un simple clic de
# bouton), ce qui ramenait l'utilisateur au premier onglet après avoir
# généré un rapport. Cette navigation "faite maison" stocke l'onglet
# actif dans session_state, qui lui persiste toujours correctement.
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "quality"

_TAB_LABELS = {
    "quality": "🧹 " + ("Qualité" if st.session_state.ui_lang == "fr" else "Quality"),
    "overview": "👀 " + ("Vue d'ensemble" if st.session_state.ui_lang == "fr" else "Overview"),
    "viz": "📊 " + ("Visualisations" if st.session_state.ui_lang == "fr" else "Visualizations"),
    "insights": "🧠 " + ("Insights" if st.session_state.ui_lang == "fr" else "Insights"),
    "report": "📄 " + ("Rapport" if st.session_state.ui_lang == "fr" else "Report"),
}

_nav_cols = st.columns(len(_TAB_LABELS))
for _col, (_key, _label) in zip(_nav_cols, _TAB_LABELS.items()):
    with _col:
        if st.button(
            _label,
            key=f"nav_btn_{_key}",
            type="primary" if st.session_state.active_tab == _key else "secondary",
            use_container_width=True,
        ):
            st.session_state.active_tab = _key
            st.rerun()

st.markdown("---")


# ==========================================
# TAB 1: QUALITÉ DES DONNÉES (TRADUIT)
# ==========================================
if st.session_state.active_tab == "quality":
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
    

    # ==========================================
    # ✅ RAPPORT DÉTAILLÉ DES ANOMALIES
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
        
        # Colonnes quasi-vides (90-99%, exclut les 100% déjà listées ci-dessus)
        if anomaly_report['quasi_empty_columns']['count'] > 0:
            with st.expander(
                f"⚠️ {anomaly_report['quasi_empty_columns']['count']} Colonne(s) Quasi-Vides (90-99%)" 
                if st.session_state.ui_lang == "fr"
                else f"⚠️ {anomaly_report['quasi_empty_columns']['count']} Quasi-Empty Column(s) (90-99%)",
                expanded=False
            ):
                cols_str = ", ".join(anomaly_report['quasi_empty_columns']['columns'])
                st.write(cols_str)
                st.caption(
                    "Ces colonnes ont entre 90% et 99% de valeurs manquantes (hors 100%, listées ci-dessus) et seront exclues des visualisations."
                    if st.session_state.ui_lang == "fr"
                    else "These columns have between 90% and 99% missing values (100% listed above) and will be excluded from visualizations."
                )
        
        # Doublons
        if anomaly_report['duplicates']['count'] > 0:
            st.warning(
                f"🔄 {anomaly_report['duplicates']['count']:,} ligne(s) dupliquée(s) ({anomaly_report['duplicates']['percentage']:.1f}%)"
                if st.session_state.ui_lang == "fr"
                else f"🔄 {anomaly_report['duplicates']['count']:,} duplicate row(s) ({anomaly_report['duplicates']['percentage']:.1f}%)"
            )
        
        # Valeurs manquantes importantes (50-89%, exclut ≥90% déjà listées ci-dessus)
        if anomaly_report['high_missing_values']:
            with st.expander(
                f"📊 {len(anomaly_report['high_missing_values'])} Colonne(s) avec 50-89% de Valeurs Manquantes"
                if st.session_state.ui_lang == "fr"
                else f"📊 {len(anomaly_report['high_missing_values'])} Column(s) with 50-89% Missing Values",
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
if st.session_state.active_tab == "overview":
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

        all_cat_cols = analysis.get("categorical_summary", {})
        analyzed_count = len(all_cat_cols)
        total_cat_cols_in_data = len(analysis.get("categorical_cols", []))
        shown_cat_cols = list(all_cat_cols.items())[:5]

        if total_cat_cols_in_data > analyzed_count:
            st.caption(
                f"ℹ️ Analyse limitée aux {analyzed_count} premières variables catégorielles sur {total_cat_cols_in_data} au total dans le fichier."
                if st.session_state.ui_lang == "fr"
                else f"ℹ️ Analysis limited to the first {analyzed_count} categorical variables out of {total_cat_cols_in_data} total in the file."
            )

        if analyzed_count > 5:
            st.caption(
                f"ℹ️ Affichage des 5 premières variables analysées sur {analyzed_count}."
                if st.session_state.ui_lang == "fr"
                else f"ℹ️ Showing the first 5 analyzed variables out of {analyzed_count}."
            )

        for col_name, info in shown_cat_cols:
            with st.expander(f"📌 {col_name}"):
                top_values = info.get("top_values", [])
                unique_count = info.get("unique_count", len(top_values))
                if top_values:
                    dist_df = pd.DataFrame(
                        top_values,
                        columns=[
                            "Catégorie" if st.session_state.ui_lang == "fr" else "Category",
                            "Nombre" if st.session_state.ui_lang == "fr" else "Count"
                        ]
                    )
                    st.dataframe(dist_df, use_container_width=True)
                    if unique_count > len(top_values):
                        st.caption(
                            f"ℹ️ Top {len(top_values)} affiché(es) sur {unique_count} catégories uniques au total."
                            if st.session_state.ui_lang == "fr"
                            else f"ℹ️ Showing top {len(top_values)} out of {unique_count} unique categories total."
                        )


# ==========================================
# TAB 3: VISUALISATIONS
# ==========================================
if st.session_state.active_tab == "viz":
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
        from utils.chart_curator import select_featured_charts, get_viz_title

        if st.session_state.get("featured_charts") is None or st.session_state.get("_featured_for") != st.session_state._last_uploaded_name:
            api_key = st.secrets.get("anthropic", {}).get("api_key", "")
            st.session_state.featured_charts = select_featured_charts(
                visualizations, api_key, lang=st.session_state.report_lang
            )
            st.session_state._featured_for = st.session_state._last_uploaded_name

        featured = st.session_state.featured_charts
        featured_keys = {item["key"] for item in featured}

        # ==========================================
        # 🌟 GRAPHIQUES COUP DE CŒUR
        # ==========================================
        st.subheader(
            "🌟 Graphiques coup de cœur" if st.session_state.ui_lang == "fr" else "🌟 Featured charts"
        )
        st.caption(
            "Sélection des visualisations les plus parlantes pour ce dataset."
            if st.session_state.ui_lang == "fr"
            else "The most insightful visualizations for this dataset."
        )

        for item in featured:
            key = item["key"]
            if key not in visualizations:
                continue
            fig, interpretation = visualizations[key]

            st.markdown(f"#### {get_viz_title(key, st.session_state.report_lang)}")
            st.pyplot(fig, use_container_width=True)

            if item.get("reason"):
                st.markdown(
                    f'<div class="insight-box">🌟 {item["reason"]}</div>',
                    unsafe_allow_html=True
                )
            if interpretation:
                st.markdown(
                    f'<div class="insight-box">💡 {interpretation}</div>',
                    unsafe_allow_html=True
                )
            st.markdown("---")

        # ==========================================
        # 📊 TOUS LES GRAPHIQUES (exhaustif, replié)
        # Réservé aux plans sans limite de visualisations (Trial = 4,
        # déjà entièrement couvert par les "coup de cœur" ci-dessus).
        # ==========================================
        from utils.plans_config import get_plan as _get_plan_viz
        _viz_limit = _get_plan_viz(st.session_state.get("user_plan", "trial"))["max_visualizations"]
        remaining = {k: v for k, v in visualizations.items() if k not in featured_keys}

        if _viz_limit == -1 and remaining:
            with st.expander(
                f"📊 Voir tous les graphiques ({len(remaining)} de plus)"
                if st.session_state.ui_lang == "fr"
                else f"📊 See all charts ({len(remaining)} more)",
                expanded=False,
            ):
                for viz_name, (fig, interpretation) in remaining.items():
                    st.subheader(get_viz_title(viz_name, st.session_state.report_lang))
                    st.pyplot(fig, use_container_width=True)

                    if interpretation:
                        st.markdown(
                            f'<div class="insight-box">💡 {interpretation}</div>',
                            unsafe_allow_html=True
                        )
                    st.markdown("---")
        elif _viz_limit != -1 and remaining:
            st.info(
                f"🔒 {len(remaining)} graphique(s) supplémentaire(s) disponible(s) avec le plan Pro."
                if st.session_state.ui_lang == "fr"
                else f"🔒 {len(remaining)} more chart(s) available with the Pro plan."
            )


# ==========================================
# TAB 4: INSIGHTS IA
# ==========================================
if st.session_state.active_tab == "insights":
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
        ai_mode = "Anthropic API"  # Mode fixe pour cette version
        if ai_mode == "Anthropic API" and api_key:
            st.info("🧠 Mode Anthropic (Service IA inclus)")
            st.success("✅ Service IA activé")
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
            
        elif ai_mode == "Anthropic API" and not api_key:
                st.warning(
                    "⚠️ Clé API requise pour le mode Anthropic" 
                    if st.session_state.ui_lang == "fr"
                    else "⚠️ API key required for Anthropic mode"
                )
        # ==========================================
        else:
            st.info("💡 Mode basique (sans IA)"
                if st.session_state.ui_lang == "fr"
                else "💡 Basic mode (no AI)"
            )
                
    
    with colB:
        can_generate = api_key is not None
        
        if st.button("🚀 Générer les Insights IA" if st.session_state.ui_lang == "fr" else "🚀 Generate AI Insights"):
            st.session_state.active_tab = "insights"  # par sécurité, garantit qu'on reste ici
            is_example = st.session_state.get("_use_example_file", False)

            # ==========================================
            # ✅ VÉRIFIER QUOTA AVANT GÉNÉRATION
            # (sauf pour le dataset d'exemple, toujours gratuit)
            # =========================================
            if is_example:
                can_generate_report_bool, quota_message = True, (
                    "Rapport d'exemple — gratuit, ne compte pas dans votre quota."
                    if st.session_state.ui_lang == "fr"
                    else "Example report — free, does not count toward your quota."
                )
            else:
                can_generate_report_bool, quota_message = can_generate_report()
            
            if not can_generate_report_bool:
                # Quota épuisé
                show_upgrade_message()
                st.stop()
            
            if not api_key:
                st.error(
                    "❌ Service IA non disponible. Contactez l'administrateur." 
                    if st.session_state.ui_lang == "fr"
                    else "❌ AI service unavailable. Contact administrator."
                )
                st.stop()
            
            # Afficher message si essai gratuit
            if quota_message:
                st.info(f"💡 {quota_message}")
            
            with st.spinner(
                "🧠 Claude analyse vos données... (30-60 secondes)" 
                if st.session_state.ui_lang == "fr" 
                else "🧠 Claude is analyzing your data... (30-60 seconds)"
            ):
                try:
                    st.session_state.ai_insights = generate_ai_insights(
                        analysis, 
                        api_key, 
                        lang=st.session_state.report_lang
                    )
                    st.session_state.chat_history = []  # nouveau rapport = nouvelle conversation
                    
                    st.success(
                        "✅ Insights générés !" 
                        if st.session_state.ui_lang == "fr" 
                        else "✅ Insights generated!"
                    )
                    
                    # ==========================================
                    # ✅ INCRÉMENTER LE COMPTEUR DE RAPPORTS
                    # (sauf pour le dataset d'exemple)
                    # ==========================================
                    if not is_example:
                        increment_report_count()
                    
                    # Afficher quota restant
                    from utils.auth_supabase import get_quota_info
                    quota = get_quota_info()
                    if is_example:
                        st.info(
                            "🎯 Rapport d'exemple généré — gratuit, non déduit de votre quota."
                            if st.session_state.ui_lang == "fr"
                            else "🎯 Example report generated — free, not deducted from your quota."
                        )
                    elif quota["is_trial"]:
                        st.info(f"🎁 Essai gratuit : {quota['remaining']} rapport(s) restant(s)")
                    # Pas de st.rerun() ici volontairement : st.rerun() réinitialise
                    # l'onglet actif au premier (limitation de st.tabs()). Le script
                    # continue naturellement et affiche les insights plus bas, sur
                    # le même onglet Insights.
                
                except Exception as e:
                    st.error(f"❌ Claude API: {str(e)}")

                    error_str = str(e).lower()

                    if "timeout" in error_str:
                        st.info(
                            "💡 Le service met du temps à répondre. Réessayez dans un instant."
                            if st.session_state.ui_lang == "fr"
                            else "💡 The service is slow to respond. Try again shortly."
                        )
                    elif "json" in error_str:
                        st.info(
                            "💡 Réponse invalide du modèle. Réessayez."
                            if st.session_state.ui_lang == "fr"
                            else "💡 Invalid model response. Please retry."
                        )
                    elif "api key" in error_str or "401" in error_str:
                        st.info(
                            "💡 Vérifiez votre clé API sur console.anthropic.com"
                            if st.session_state.ui_lang == "fr"
                            else "💡 Check your API key at console.anthropic.com"
                        )

                    # ==========================================
                    # ✅ FILET DE SÉCURITÉ : mode basique si l'API échoue
                    # Ne compte PAS dans le quota — l'échec n'est pas
                    # imputable à l'utilisateur (transparence).
                    # ==========================================
                    st.warning(
                        "⚠️ Basculement en mode basique (sans IA) suite à l'échec de l'API. "
                        "**Ce rapport ne sera pas déduit de votre quota.**"
                        if st.session_state.ui_lang == "fr"
                        else "⚠️ Falling back to basic mode (no AI) after the API failure. "
                        "**This report will not be deducted from your quota.**"
                    )
                    try:
                        st.session_state.ai_insights = generate_basic_insights(
                            analysis,
                            lang=st.session_state.report_lang
                        )
                        st.session_state.chat_history = []
                        # Pas d'increment_report_count() ni de st.rerun() ici,
                        # volontairement (voir note plus haut sur st.tabs()).
                    except Exception as fallback_error:
                        st.error(f"❌ {fallback_error}")
    
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
        # 💬 CHAT CONVERSATIONNEL SUR LE RAPPORT
        # ==========================================
        st.markdown("---")
        st.subheader(
            "💬 Poser une question sur ce rapport"
            if st.session_state.ui_lang == "fr"
            else "💬 Ask a question about this report"
        )
        st.caption(
            "Discutez avec l'IA à partir des statistiques et du rapport déjà générés (pas des lignes brutes du fichier)."
            if st.session_state.ui_lang == "fr"
            else "Chat with the AI based on the statistics and report already generated (not the raw file rows)."
        )

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = []

        if st.session_state.chat_history:
            if st.button(
                "🗑️ Effacer la conversation" if st.session_state.ui_lang == "fr" else "🗑️ Clear conversation",
                key="clear_chat_btn",
            ):
                st.session_state.chat_history = []
                # Pas de st.rerun() : la boucle d'affichage juste en dessous
                # reflète déjà la liste vide dans cette même exécution.

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        user_question = st.chat_input(
            "Posez votre question..." if st.session_state.ui_lang == "fr" else "Ask your question..."
        )

        if user_question:
            st.session_state.chat_history.append({"role": "user", "content": user_question})
            with st.chat_message("user"):
                st.markdown(user_question)

            with st.chat_message("assistant"):
                with st.spinner("..."):
                    try:
                        from utils.report_chat import chat_about_report
                        api_key = st.secrets.get("anthropic", {}).get("api_key", "")
                        reply = chat_about_report(
                            analysis=analysis,
                            ai_insights=insights,
                            chat_history=st.session_state.chat_history[:-1],  # sans la dernière question (déjà passée en user_question)
                            user_question=user_question,
                            api_key=api_key,
                            lang=st.session_state.report_lang,
                        )
                        st.markdown(reply)
                        st.session_state.chat_history.append({"role": "assistant", "content": reply})
                    except Exception as e:
                        error_reply = f"❌ {e}"
                        st.error(error_reply)
                        st.session_state.chat_history.append({"role": "assistant", "content": error_reply})


# ==========================================
# TAB 5: RAPPORT FINAL
# ==========================================
if st.session_state.active_tab == "report":
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

            from utils.plans_config import get_plan as _get_plan_pdf
            if "PDF" in _get_plan_pdf(st.session_state.get("user_plan", "trial"))["export_formats"]:
                st.caption(
                    "💡 Pour obtenir un PDF : téléchargez le fichier HTML ci-dessous, ouvrez-le dans votre navigateur, puis Ctrl+P (ou Cmd+P sur Mac) → \"Enregistrer en PDF\"."
                    if st.session_state.ui_lang == "fr"
                    else "💡 To get a PDF: download the HTML file below, open it in your browser, then Ctrl+P (or Cmd+P on Mac) → \"Save as PDF\"."
                )

            _word_allowed = "Word" in _get_plan_pdf(st.session_state.get("user_plan", "trial"))["export_formats"]
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
                if not _word_allowed:
                    st.button(
                        "🔒 Word (Plan Pro)" if st.session_state.ui_lang == "fr" else "🔒 Word (Pro plan)",
                        use_container_width=True,
                        disabled=True,
                        help="Passez au plan Pro pour débloquer l'export Word." if st.session_state.ui_lang == "fr" else "Upgrade to Pro to unlock Word export."
                    )
                elif st.button(
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
