"""
Sélection des graphiques "coup de cœur" — l'IA choisit 3-4 visualisations
parmi celles disponibles qui racontent le mieux l'histoire du dataset,
plutôt que de tout montrer de façon exhaustive.

Appel API léger : seuls les noms de graphiques + leurs interprétations
textuelles sont envoyés (jamais les images), donc rapide et peu coûteux.
En cas d'échec API, un ordre de priorité par défaut prend le relais
(l'onglet ne casse jamais).
"""

import json
import requests
from typing import Dict, Tuple, List, Any
import matplotlib.pyplot as plt

ANTHROPIC_MODEL = "claude-sonnet-4-5-20250929"

MAX_FEATURED = 4

# Ordre de priorité par défaut si l'IA n'est pas disponible —
# du plus généralement "parlant" au plus niche.
DEFAULT_PRIORITY = [
    "correlation_matrix",
    "continuous_distributions",
    "categorical_distribution",
    "outlier_detection",
    "discrete_distributions",
    "grouped_analysis",
    "relationship_scatter",
    "categorical_analysis",
]

VIZ_TITLES = {
    "continuous_distributions": {"fr": "Distributions des variables continues", "en": "Continuous variable distributions"},
    "discrete_distributions": {"fr": "Distributions des variables discrètes", "en": "Discrete variable distributions"},
    "outlier_detection": {"fr": "Détection des valeurs aberrantes", "en": "Outlier detection"},
    "correlation_matrix": {"fr": "Matrice de corrélation", "en": "Correlation matrix"},
    "categorical_analysis": {"fr": "Analyse catégorielle", "en": "Categorical analysis"},
    "relationship_scatter": {"fr": "Relation entre variables", "en": "Variable relationship"},
    "grouped_analysis": {"fr": "Analyse groupée", "en": "Grouped analysis"},
    "categorical_distribution": {"fr": "Distribution catégorielle", "en": "Categorical distribution"},
}


def _default_selection(available_keys: List[str]) -> List[Dict[str, str]]:
    """Sélection de repli sans IA, basée sur l'ordre de priorité par défaut."""
    ordered = [k for k in DEFAULT_PRIORITY if k in available_keys]
    ordered += [k for k in available_keys if k not in ordered]  # au cas où
    return [{"key": k, "reason": ""} for k in ordered[:MAX_FEATURED]]


def select_featured_charts(
    visualizations: Dict[str, Tuple[Any, str]],
    api_key: str,
    lang: str = "fr",
) -> List[Dict[str, str]]:
    """
    Retourne une liste ordonnée de {"key": viz_name, "reason": "..."} pour
    les graphiques sélectionnés comme les plus pertinents.

    Args:
        visualizations: dict {viz_name: (figure, interpretation_text)}
        api_key: clé API Anthropic
        lang: 'fr' ou 'en'
    """
    available_keys = list(visualizations.keys())

    if not available_keys:
        return []

    if len(available_keys) <= MAX_FEATURED:
        # Pas besoin de choisir, il y en a déjà peu — tout est "featured"
        return [{"key": k, "reason": ""} for k in available_keys]

    if not api_key:
        return _default_selection(available_keys)

    charts_summary = "\n".join(
        f"- {key}: {interp[:300]}"
        for key, (_, interp) in visualizations.items()
    )

    lang_instruction = "en français" if lang == "fr" else "in English"

    prompt = f"""You are a data storytelling expert. Below is a list of available charts for a dataset, each with its automatically generated interpretation.

{charts_summary}

Select the {MAX_FEATURED} charts that best tell the overall story of this dataset for a general, non-technical audience — prioritize charts that are the most insightful or surprising, not necessarily the most technical.

Respond ONLY with a valid JSON array (no markdown, no preamble), ordered from most to least important, in this exact format:
[
  {{"key": "exact_chart_key_from_the_list_above", "reason": "one short sentence {lang_instruction} explaining why this chart matters"}}
]"""

    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    data = {
        "model": ANTHROPIC_MODEL,
        "max_tokens": 500,
        "temperature": 0.3,
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data,
            timeout=30,
        )
        if response.status_code != 200:
            return _default_selection(available_keys)

        result = response.json()
        text = result["content"][0]["text"].strip()
        text = text.replace("```json", "").replace("```", "").strip()
        selection = json.loads(text)

        # Ne garder que les clés qui existent réellement (sécurité anti-hallucination)
        valid_selection = [
            item for item in selection
            if isinstance(item, dict) and item.get("key") in available_keys
        ]

        if not valid_selection:
            return _default_selection(available_keys)

        return valid_selection[:MAX_FEATURED]

    except Exception:
        # Ne jamais casser l'onglet Visualisations à cause de ce choix éditorial
        return _default_selection(available_keys)


def get_viz_title(viz_key: str, lang: str = "fr") -> str:
    """Titre lisible pour une clé de visualisation."""
    titles = VIZ_TITLES.get(viz_key)
    if titles:
        return titles.get(lang, titles["fr"])
    return viz_key.replace("_", " ").title()
