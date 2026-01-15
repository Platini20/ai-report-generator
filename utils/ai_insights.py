"""
Module unifié de génération d'insights IA
Supporte 3 modes : Basique, Ollama Local, Anthropic API
VERSION FINALE : Haiku + Contexte Anomalies + Switch facile Sonnet
"""

import json
import requests
import pandas as pd
from typing import Dict, Any, Optional, Tuple

# ==========================================
# ✅ CONFIGURATION DU MODÈLE ANTHROPIC
# ==========================================

#ANTHROPIC_MODEL = "claude-3-haiku-20240307"  # Rapide, économique, fiable
ANTHROPIC_MODEL = "claude-sonnet-4-5-20250929"  # Plus puissant, plus cher

# Pour changer : décommentez la ligne Sonnet et commentez Haiku

# ==========================================
# MODE 1 : ANTHROPIC API (Cloud)
# ==========================================

def generate_ai_insights(analysis: Dict[str, Any], api_key: str, lang: str = 'fr') -> Dict[str, Any]:
    """
    Génère des insights avec Claude IA via l'API Anthropic
    ✅ Utilise le modèle défini dans ANTHROPIC_MODEL
    ✅ Intègre le rapport d'anomalies si disponible
    
    Args:
        analysis: Dictionnaire d'analyse du dataframe (peut contenir 'anomaly_report')
        api_key: Clé API Anthropic
        lang: Langue ('fr' ou 'en')
        
    Returns:
        dict: Insights générés par l'IA au format standard
    """
    try:
        # Préparer le résumé des statistiques
        stats_text = ""
        if 'numeric_stats' in analysis and not analysis['numeric_stats'].empty:
            stats_text = f"Statistics:\n{analysis['numeric_stats'].to_string()[:800]}"
        
        lang_instruction = "en français" if lang == 'fr' else "in English"
        
        # Résumé des données
        stats_summary = f"""
Dataset Overview:
- Rows: {analysis['shape'][0]}
- Columns: {analysis['shape'][1]}
- Numeric columns ({len(analysis['numeric_cols'])}): {', '.join(analysis['numeric_cols'][:8])}
- Categorical columns ({len(analysis['categorical_cols'])}): {', '.join(analysis['categorical_cols'][:5])}

{stats_text}
"""
        
        # ✅ Ajouter contexte d'anomalies si disponible
        anomaly_context = ""
        if 'anomaly_report' in analysis:
            anomaly_rep = analysis['anomaly_report']
            
            # Construire le contexte d'anomalies
            anomaly_parts = []
            
            if anomaly_rep['empty_columns']['count'] > 0:
                cols = ', '.join(anomaly_rep['empty_columns']['columns'][:5])
                if anomaly_rep['empty_columns']['count'] > 5:
                    cols += f" (+{anomaly_rep['empty_columns']['count'] - 5} more)"
                anomaly_parts.append(f"- {anomaly_rep['empty_columns']['count']} completely empty column(s): {cols}")
            
            if anomaly_rep['quasi_empty_columns']['count'] > 0:
                cols = ', '.join(anomaly_rep['quasi_empty_columns']['columns'][:5])
                if anomaly_rep['quasi_empty_columns']['count'] > 5:
                    cols += f" (+{anomaly_rep['quasi_empty_columns']['count'] - 5} more)"
                anomaly_parts.append(f"- {anomaly_rep['quasi_empty_columns']['count']} quasi-empty column(s) (≥90% missing): {cols}")
            
            if anomaly_rep['duplicates']['count'] > 0:
                anomaly_parts.append(f"- {anomaly_rep['duplicates']['count']} duplicate row(s) ({anomaly_rep['duplicates']['percentage']:.1f}%)")
            
            if anomaly_rep['high_missing_values']:
                high_miss = ', '.join([f"{item['column']} ({item['percentage']:.1f}%)" 
                                      for item in anomaly_rep['high_missing_values'][:3]])
                if len(anomaly_rep['high_missing_values']) > 3:
                    high_miss += f" (+{len(anomaly_rep['high_missing_values']) - 3} more)"
                anomaly_parts.append(f"- High missing values (>50%): {high_miss}")
            
            if anomaly_parts:
                anomaly_context = f"""

DATA QUALITY ISSUES DETECTED:
{chr(10).join(anomaly_parts)}

IMPORTANT: Your analysis MUST mention these data quality issues in the "anomalies" section.
These are REAL problems detected in the data, not generic statements.
"""
        
        # Prompt structuré pour Claude
        prompt = f"""You are an expert data analyst. Analyze this dataset and provide a professional analysis report {lang_instruction}.

{stats_summary}
{anomaly_context}

IMPORTANT: Respond ONLY with a valid JSON object (no markdown, no preamble) with this EXACT structure:

{{
  "resume_executif": "2-3 sentence executive summary",
  "tendances_principales": [
    "main trend 1",
    "main trend 2",
    "main trend 3"
  ],
  "insights": [
    {{
      "titre": "Insight Title 1",
      "description": "Detailed explanation of this insight"
    }},
    {{
      "titre": "Insight Title 2",
      "description": "Detailed explanation of this insight"
    }}
  ],
  "anomalies": [
    "specific anomaly description based on data quality issues detected above"
  ],
  "recommandations": [
    {{
      "action": "Recommended action 1",
      "justification": "Why this action is recommended"
    }},
    {{
      "action": "Recommended action 2",
      "justification": "Why this action is recommended"
    }}
  ],
  "conclusion": "2-3 sentence conclusion"
}}

Generate the analysis now:"""
        
        # Configuration de la requête API
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        data = {
            "model": ANTHROPIC_MODEL,  # ✅ Utilise la constante (Haiku ou Sonnet)
            "max_tokens": 3000,
            "temperature": 0.7,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        # Appel API avec retry
        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    "https://api.anthropic.com/v1/messages",
                    headers=headers,
                    json=data,
                    timeout=60
                )
                
                # Gestion des erreurs HTTP
                if response.status_code == 401:
                    error_msg = "🔑 Clé API invalide" if lang == 'fr' else "🔑 Invalid API key"
                    raise Exception(f"{error_msg}. Check your key at console.anthropic.com")
                    
                elif response.status_code == 429:
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(2)
                        continue
                    error_msg = "⏰ Limite de taux atteinte" if lang == 'fr' else "⏰ Rate limit reached"
                    raise Exception(f"{error_msg}. Please wait and try again.")
                    
                elif response.status_code != 200:
                    raise Exception(f"API error {response.status_code}: {response.text[:200]}")
                
                # Parse de la réponse
                result = response.json()
                
                if 'content' not in result or not result['content']:
                    raise Exception("Empty response from API")
                
                text = result['content'][0]['text'].strip()
                
                # Nettoyage du JSON (enlever les markdown artifacts)
                text = text.replace('```json', '').replace('```', '').strip()
                
                # Parse et validation du JSON
                insights = json.loads(text)
                
                # Validation des champs obligatoires
                required_fields = ['resume_executif', 'tendances_principales', 'insights', 
                                 'anomalies', 'recommandations', 'conclusion']
                
                for field in required_fields:
                    if field not in insights:
                        insights[field] = [] if field in ['tendances_principales', 'insights', 
                                                          'anomalies', 'recommandations'] else ""
                
                return insights
                
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    continue
                error_msg = "⏰ Délai d'attente dépassé" if lang == 'fr' else "⏰ Request timeout"
                raise Exception(f"{error_msg}. The API took too long to respond.")
                
            except requests.exceptions.ConnectionError:
                error_msg = "🌐 Erreur réseau" if lang == 'fr' else "🌐 Network error"
                raise Exception(f"{error_msg}. Check your internet connection.")
        
    except json.JSONDecodeError as e:
        error_msg = "📄 Réponse JSON invalide" if lang == 'fr' else "📄 Invalid JSON response"
        raise Exception(f"{error_msg}: {str(e)}")
        
    except KeyError as e:
        error_msg = "🔧 Format de réponse inattendu" if lang == 'fr' else "🔧 Unexpected API response format"
        raise Exception(f"{error_msg}: {str(e)}")
        
    except Exception as e:
        # Re-raise avec message clair
        if "Invalid API key" in str(e) or "Rate limit" in str(e):
            raise
        error_msg = "❌ Erreur" if lang == 'fr' else "❌ Error"
        raise Exception(f"{error_msg}: {str(e)}")


def test_api_key(api_key: str) -> Tuple[bool, str]:
    """
    Test la validité d'une clé API Anthropic
    ✅ Utilise le modèle défini dans ANTHROPIC_MODEL
    
    Args:
        api_key: Clé API à tester
        
    Returns:
        tuple: (is_valid, message)
    """
    try:
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        data = {
            "model": ANTHROPIC_MODEL,  # ✅ Utilise la constante
            "max_tokens": 10,
            "messages": [{"role": "user", "content": "test"}]
        }
        
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data,
            timeout=10
        )
        
        if response.status_code == 200:
            # Indiquer quel modèle est utilisé
            model_name = "Haiku" if "haiku" in ANTHROPIC_MODEL else "Sonnet"
            return True, f"✅ API key valid ({model_name} model)"
        elif response.status_code == 401:
            return False, "❌ Invalid API key"
        else:
            return False, f"⚠️ API returned status {response.status_code}"
            
    except Exception as e:
        return False, f"❌ Error testing API key: {str(e)}"


# ==========================================
# MODE 2 : OLLAMA LOCAL
# ==========================================

def llm_insights_local(df: pd.DataFrame, analysis: Dict[str, Any], 
                      lang: str = 'fr', model: str = 'llama3.2:3b') -> Dict[str, Any]:
    """
    Génère des insights avec un LLM local (Ollama)
    ✅ Intègre le rapport d'anomalies si disponible
    
    Args:
        df: DataFrame pandas
        analysis: Dictionnaire d'analyse de base (peut contenir 'anomaly_report')
        lang: Langue ('fr' ou 'en')
        model: Nom du modèle Ollama à utiliser
        
    Returns:
        dict: Insights au format standard
    """
    try:
        # Préparer les statistiques
        stats_text = ""
        if 'numeric_stats' in analysis and not analysis['numeric_stats'].empty:
            stats_text = f"Statistics:\n{analysis['numeric_stats'].to_string()[:600]}"
        
        lang_instruction = "en français" if lang == 'fr' else "in English"
        
        # Résumé des données
        stats_summary = f"""
Dataset Analysis:
- Rows: {analysis['shape'][0]}
- Columns: {analysis['shape'][1]}
- Numeric columns ({len(analysis['numeric_cols'])}): {', '.join(analysis['numeric_cols'][:5])}
- Categorical columns ({len(analysis['categorical_cols'])}): {', '.join(analysis['categorical_cols'][:3])}

{stats_text}
"""
        
        # ✅ Ajouter contexte d'anomalies si disponible
        anomaly_context = ""
        if 'anomaly_report' in analysis:
            anomaly_rep = analysis['anomaly_report']
            
            anomaly_parts = []
            if anomaly_rep['empty_columns']['count'] > 0:
                anomaly_parts.append(f"Empty columns: {anomaly_rep['empty_columns']['count']}")
            if anomaly_rep['quasi_empty_columns']['count'] > 0:
                anomaly_parts.append(f"Quasi-empty (≥90%): {anomaly_rep['quasi_empty_columns']['count']}")
            if anomaly_rep['duplicates']['count'] > 0:
                anomaly_parts.append(f"Duplicates: {anomaly_rep['duplicates']['count']}")
            
            if anomaly_parts:
                anomaly_context = f"\n\nData issues: {', '.join(anomaly_parts)}\nMention these in 'anomalies' field."
        
        # Prompt structuré
        prompt = f"""Tu es un analyste de données expert. Analyse ce dataset et fournis un rapport professionnel {lang_instruction}.

{stats_summary}{anomaly_context}

Réponds UNIQUEMENT avec un objet JSON (pas de texte avant ou après, pas de markdown) avec cette structure EXACTE:
{{
  "resume_executif": "résumé en 2-3 phrases",
  "tendances_principales": ["tendance 1", "tendance 2", "tendance 3"],
  "insights": [
    {{"titre": "Insight 1", "description": "explication détaillée"}},
    {{"titre": "Insight 2", "description": "explication détaillée"}}
  ],
  "anomalies": ["anomalie ou 'Aucune anomalie détectée'"],
  "recommandations": [
    {{"action": "Action 1", "justification": "pourquoi"}},
    {{"action": "Action 2", "justification": "pourquoi"}}
  ],
  "conclusion": "conclusion en 2-3 phrases"
}}"""
        
        # Appeler Ollama
        from utils.local_llm import get_model_timeout
        timeout = get_model_timeout(model)
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {
                    "temperature": 0.7,
                    "num_predict": 2000
                }
            },
            timeout=timeout
        )
        
        if response.status_code != 200:
            raise Exception(f"Ollama returned status {response.status_code}")
        
        result = response.json()
        text = result.get('response', '{}').strip()
        
        # Nettoyer le JSON
        if text.startswith('```json'):
            text = text.replace('```json', '').replace('```', '').strip()
        elif text.startswith('```'):
            text = text.replace('```', '').strip()
        
        # Parser le JSON
        insights = json.loads(text)
        
        # Validation des champs obligatoires
        required_fields = ['resume_executif', 'tendances_principales', 'insights', 
                          'anomalies', 'recommandations', 'conclusion']
        
        for field in required_fields:
            if field not in insights:
                insights[field] = [] if field in ['tendances_principales', 'insights', 
                                                  'anomalies', 'recommandations'] else ""
        
        return insights
        
    except requests.exceptions.ConnectionError:
        raise Exception(
            "🔌 Ollama n'est pas lancé. Démarrez-le avec: ollama serve" 
            if lang == 'fr' 
            else "🔌 Ollama is not running. Start it with: ollama serve"
        )
    
    except requests.exceptions.Timeout:
        raise Exception(
            f"⏰ Le modèle prend trop de temps. Essayez un modèle plus petit." 
            if lang == 'fr' 
            else f"⏰ The model is taking too long. Try a smaller model."
        )
    
    except json.JSONDecodeError as e:
        raise Exception(
            f"📄 Réponse JSON invalide: {str(e)}" 
            if lang == 'fr' 
            else f"📄 Invalid JSON response: {str(e)}"
        )
    
    except Exception as e:
        raise Exception(
            f"❌ Erreur LLM local: {str(e)}" 
            if lang == 'fr' 
            else f"❌ Local LLM error: {str(e)}"
        )


# ==========================================
# MODE 3 : BASIQUE (Sans IA)
# ==========================================

def generate_basic_insights(analysis: Dict[str, Any], lang: str = 'fr') -> Dict[str, Any]:
    """
    Génère des insights basiques sans IA (fallback)
    ✅ Utilise le rapport d'anomalies si disponible
    
    Args:
        analysis: Dictionnaire d'analyse (peut contenir 'anomaly_report')
        lang: Langue ('fr' ou 'en')
        
    Returns:
        dict: Insights basiques au format standard
    """
    shape = analysis.get('shape', (0, 0))
    num_cols = analysis.get('numeric_cols', [])
    cat_cols = analysis.get('categorical_cols', [])
    
    # ✅ NOUVEAU : Utiliser le rapport d'anomalies si disponible
    anomalies_list = []
    if 'anomaly_report' in analysis:
        anomaly_rep = analysis['anomaly_report']
        
        if anomaly_rep['empty_columns']['count'] > 0:
            msg = f"{anomaly_rep['empty_columns']['count']} colonne(s) vide(s)" if lang == 'fr' else f"{anomaly_rep['empty_columns']['count']} empty column(s)"
            anomalies_list.append(msg)
        
        if anomaly_rep['quasi_empty_columns']['count'] > 0:
            msg = f"{anomaly_rep['quasi_empty_columns']['count']} colonne(s) quasi-vide(s) (≥90%)" if lang == 'fr' else f"{anomaly_rep['quasi_empty_columns']['count']} quasi-empty column(s) (≥90%)"
            anomalies_list.append(msg)
        
        if anomaly_rep['duplicates']['count'] > 0:
            msg = f"{anomaly_rep['duplicates']['count']} ligne(s) dupliquée(s)" if lang == 'fr' else f"{anomaly_rep['duplicates']['count']} duplicate row(s)"
            anomalies_list.append(msg)
    
    if not anomalies_list:
        anomalies_list = ["Aucune anomalie majeure détectée" if lang == 'fr' else "No major anomalies detected"]
    
    if lang == 'fr':
        return {
            'resume_executif': (
                f"Analyse de {shape[0]:,} observations sur {shape[1]} variables. "
                f"Le dataset contient {len(num_cols)} colonnes numériques et "
                f"{len(cat_cols)} colonnes catégorielles."
            ),
            'tendances_principales': [
                f"Dataset de {shape[0]:,} observations",
                f"{len(num_cols)} variable(s) numérique(s) identifiée(s)",
                f"{len(cat_cols)} variable(s) catégorielle(s) présente(s)"
            ],
            'insights': [
                {
                    'titre': "Composition du dataset",
                    'description': (
                        f"Le jeu de données contient {shape[1]} variables au total, "
                        f"avec une répartition de {len(num_cols)} colonnes numériques "
                        f"et {len(cat_cols)} colonnes catégorielles."
                    )
                },
                {
                    'titre': "Volume de données",
                    'description': (
                        f"Avec {shape[0]:,} observations, le dataset offre un volume "
                        f"suffisant pour des analyses statistiques robustes."
                    )
                }
            ],
            'anomalies': anomalies_list,
            'recommandations': [
                {
                    'action': "Activer l'analyse IA",
                    'justification': (
                        "Pour obtenir des insights approfondis et des recommandations "
                        "personnalisées basées sur vos données"
                    )
                },
                {
                    'action': "Vérifier la qualité des données",
                    'justification': (
                        "S'assurer qu'il n'y a pas de valeurs manquantes ou aberrantes"
                    )
                }
            ],
            'conclusion': (
                "Analyse préliminaire complétée. Activez le mode IA pour des insights avancés."
            )
        }
    else:
        return {
            'resume_executif': (
                f"Analysis of {shape[0]:,} observations across {shape[1]} variables. "
                f"{len(num_cols)} numeric and {len(cat_cols)} categorical columns."
            ),
            'tendances_principales': [
                f"Dataset with {shape[0]:,} observations",
                f"{len(num_cols)} numeric variable(s) identified",
                f"{len(cat_cols)} categorical variable(s) present"
            ],
            'insights': [
                {
                    'titre': "Dataset composition",
                    'description': (
                        f"The dataset contains {shape[1]} total variables, "
                        f"with {len(num_cols)} numeric and {len(cat_cols)} categorical columns."
                    )
                },
                {
                    'titre': "Data volume",
                    'description': (
                        f"With {shape[0]:,} observations, the dataset provides "
                        f"sufficient volume for robust statistical analysis."
                    )
                }
            ],
            'anomalies': anomalies_list,
            'recommandations': [
                {
                    'action': "Enable AI analysis",
                    'justification': (
                        "To obtain deep insights and personalized recommendations"
                    )
                },
                {
                    'action': "Check data quality",
                    'justification': (
                        "Ensure there are no missing values or outliers"
                    )
                }
            ],
            'conclusion': (
                "Preliminary analysis completed. Enable AI mode for advanced insights."
            )
        }


# ==========================================
# UTILITAIRES
# ==========================================

def normalize_insights_for_report(insights: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalise les insights vers le format attendu par les exports
    Gère les différents formats possibles
    """
    # Si déjà au bon format, retourner tel quel
    required_fields = ['resume_executif', 'tendances_principales', 'insights', 
                       'anomalies', 'recommandations', 'conclusion']
    
    if all(k in insights for k in required_fields):
        try:
            if isinstance(insights.get('insights'), list):
                for item in insights['insights']:
                    if isinstance(item, dict) and 'titre' in item and 'description' in item:
                        continue
                    else:
                        break
                else:
                    return insights
        except:
            pass
    
    # Créer la structure normalisée
    normalized = {
        'resume_executif': str(insights.get('resume_executif') or insights.get('summary') or ''),
        'tendances_principales': [],
        'insights': [],
        'anomalies': [],
        'recommandations': [],
        'conclusion': str(insights.get('conclusion') or '')
    }
    
    # Normaliser tendances
    tendances = insights.get('tendances_principales') or insights.get('trends') or []
    normalized['tendances_principales'] = [str(t) for t in tendances] if isinstance(tendances, list) else [str(tendances)]
    
    # Normaliser insights
    raw_insights = insights.get('insights') or []
    for item in raw_insights if isinstance(raw_insights, list) else []:
        if isinstance(item, dict):
            normalized['insights'].append({
                'titre': str(item.get('titre') or item.get('title') or 'Insight'),
                'description': str(item.get('description') or item.get('desc') or '')
            })
    
    # Normaliser anomalies
    anomalies = insights.get('anomalies') or []
    normalized['anomalies'] = [str(a) for a in anomalies] if isinstance(anomalies, list) else [str(anomalies)]
    
    # Normaliser recommandations
    raw_reco = insights.get('recommandations') or []
    for rec in raw_reco if isinstance(raw_reco, list) else []:
        if isinstance(rec, dict):
            normalized['recommandations'].append({
                'action': str(rec.get('action') or rec.get('recommendation') or ''),
                'justification': str(rec.get('justification') or rec.get('reason') or '')
            })
    
    return normalized
