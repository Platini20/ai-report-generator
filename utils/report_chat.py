"""
Module de chat conversationnel — questions de suivi sur un rapport déjà généré.
Chat "simple" : répond à partir des statistiques déjà calculées, ne relance
pas d'analyse pandas sur les données brutes.

Ne consomme PAS le quota de rapports — protégé uniquement par une limite
raisonnable de messages par session (MAX_CHAT_MESSAGES) pour éviter les abus.
"""

import json
import requests
from typing import Dict, Any, List

ANTHROPIC_MODEL = "claude-sonnet-4-5-20250929"  # Même modèle que ai_insights.py

MAX_CHAT_MESSAGES = 30  # Limite raisonnable par rapport, pas liée au quota payant


def _build_context_summary(analysis: Dict[str, Any], ai_insights: Dict[str, Any], lang: str) -> str:
    """Construit un résumé compact du dataset + du rapport déjà généré,
    servant de contexte au chat (mêmes stats que celles envoyées à l'IA
    pour générer le rapport initial — jamais les lignes brutes)."""

    stats_text = ""
    if 'numeric_stats' in analysis and not analysis['numeric_stats'].empty:
        stats_text = f"Statistics:\n{analysis['numeric_stats'].to_string()[:1200]}"

    stats_summary = f"""Dataset Overview:
- Rows: {analysis['shape'][0]}
- Columns: {analysis['shape'][1]}
- Numeric columns ({len(analysis['numeric_cols'])}): {', '.join(analysis['numeric_cols'][:10])}
- Categorical columns ({len(analysis['categorical_cols'])}): {', '.join(analysis['categorical_cols'][:10])}

{stats_text}"""

    report_summary = ""
    if ai_insights:
        report_summary = f"""

PREVIOUSLY GENERATED REPORT (for reference, already shown to the user):
Executive summary: {ai_insights.get('resume_executif', '')}
Main trends: {'; '.join(ai_insights.get('tendances_principales', []))}
Key insights: {'; '.join(i.get('titre', '') + ' - ' + i.get('description', '') for i in ai_insights.get('insights', []))}
Anomalies noted: {'; '.join(ai_insights.get('anomalies', []))}
Recommendations: {'; '.join(r.get('action', '') for r in ai_insights.get('recommandations', []))}"""

    return stats_summary + report_summary


def chat_about_report(
    analysis: Dict[str, Any],
    ai_insights: Dict[str, Any],
    chat_history: List[Dict[str, str]],
    user_question: str,
    api_key: str,
    lang: str = 'fr',
) -> str:
    """
    Répond à une question de suivi sur le rapport déjà généré.

    Args:
        analysis: dict d'analyse du dataframe (mêmes stats que pour le rapport initial)
        ai_insights: le rapport IA déjà généré (dict)
        chat_history: liste de {"role": "user"|"assistant", "content": str}
                      (déjà échangés dans CETTE conversation, sans la nouvelle question)
        user_question: la nouvelle question posée par l'utilisateur
        api_key: clé API Anthropic
        lang: 'fr' ou 'en'

    Returns:
        str: la réponse texte de l'IA
    """
    if len(chat_history) >= MAX_CHAT_MESSAGES:
        return (
            "⚠️ Limite de conversation atteinte pour ce rapport. Générez un nouveau rapport pour continuer à discuter."
            if lang == 'fr'
            else "⚠️ Conversation limit reached for this report. Generate a new report to keep chatting."
        )

    lang_instruction = "en français" if lang == 'fr' else "in English"
    context = _build_context_summary(analysis, ai_insights, lang)

    system_prompt = f"""You are a helpful data analyst assistant. You already produced a report for this dataset (see context below). The user is now asking follow-up questions about it.

{context}

Instructions:
- Answer {lang_instruction}, concisely and conversationally (a few sentences, not a full report).
- Base your answers ONLY on the statistics and report summary above — you do NOT have access to the raw data rows.
- If the user asks something that would require the raw data (e.g. filtering to a specific subgroup, exact row-level values) and it's not derivable from the statistics provided, say so honestly rather than inventing numbers, and suggest they could re-upload a filtered version of their file if they need that level of detail.
- Do not repeat the entire original report; focus on directly answering the new question."""

    messages = list(chat_history) + [{"role": "user", "content": user_question}]

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }

    data = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 600,
        "temperature": 0.5,
        "system": system_prompt,
        "messages": messages,
    }

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data,
            timeout=45,
        )

        if response.status_code == 401:
            raise Exception(
                "🔑 Clé API invalide. Vérifiez-la sur console.anthropic.com"
                if lang == 'fr'
                else "🔑 Invalid API key. Check it at console.anthropic.com"
            )
        elif response.status_code == 429:
            raise Exception(
                "⏰ Limite de taux atteinte, réessayez dans un instant."
                if lang == 'fr'
                else "⏰ Rate limit reached, please try again shortly."
            )
        elif response.status_code != 200:
            raise Exception(f"API error {response.status_code}: {response.text[:200]}")

        result = response.json()
        if 'content' not in result or not result['content']:
            raise Exception("Empty response from API")

        return result['content'][0]['text'].strip()

    except requests.exceptions.Timeout:
        raise Exception(
            "⏰ Délai d'attente dépassé, réessayez."
            if lang == 'fr'
            else "⏰ Request timeout, please try again."
        )
    except requests.exceptions.ConnectionError:
        raise Exception(
            "🌐 Erreur réseau, vérifiez votre connexion."
            if lang == 'fr'
            else "🌐 Network error, check your connection."
        )
