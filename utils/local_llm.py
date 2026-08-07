"""
Module Ollama - CORRECTION : Logique timeout pour petits modèles
Version complète corrigée
"""

import requests
import json
from typing import List, Dict, Any, Optional, Tuple


def check_ollama_available() -> bool:
    """Vérifie si Ollama est disponible"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False


def list_ollama_models() -> List[str]:
    """Liste les modèles Ollama disponibles"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            
            model_names = []
            for model in models:
                name = model.get('name', '') or model.get('model', '')
                if name:
                    model_names.append(name)
            
            return model_names
        return []
    except:
        return []


def get_model_timeout(model_name: str) -> int:
    """
    Retourne le timeout adapté au modèle
    CORRECTION : Prioriser la taille (1b, 3b) AVANT :latest
    
    Args:
        model_name: Nom du modèle
        
    Returns:
        int: Timeout en secondes
    """
    model_lower = model_name.lower()
    
    # PRIORITÉ 1 : Petits modèles (même si :latest)
    if '1b' in model_lower:
        return 240  # 4 minutes (modèles 1B sont rapides)
    
    elif '3b' in model_lower or 'mini' in model_lower:
        return 300  # 5 minutes (modèles 3B)
    
    # PRIORITÉ 2 : Gros modèles connus
    elif any(x in model_lower for x in ['7b', '8b', '13b']):
        return 600  # 10 minutes
    
    # PRIORITÉ 3 : :latest (on ne connaît pas la taille)
    elif 'latest' in model_lower:
        # Deviner selon le nom de base
        if 'mistral' in model_lower or 'llama3.1' in model_lower:
            return 600  # 10 minutes (probablement 7B+)
        else:
            return 420  # 7 minutes (prudent)
    
    # Par défaut
    else:
        return 360  # 6 minutes


def estimate_generation_time(model_name: str) -> str:
    """
    Estime le temps de génération
    CORRECTION : Prioriser taille AVANT :latest
    """
    model_lower = model_name.lower()
    
    # Petits modèles
    if '1b' in model_lower:
        return "~30-60 secondes"
    elif '3b' in model_lower or 'mini' in model_lower:
        return "~1-2 minutes"
    
    # Gros modèles
    elif any(x in model_lower for x in ['7b', '8b', '13b']):
        return "~3-5 minutes"
    
    # :latest (deviner)
    elif 'latest' in model_lower:
        if 'mistral' in model_lower or 'llama3.1' in model_lower:
            return "~3-5 minutes (gros modèle)"
        else:
            return "~2-3 minutes"
    
    else:
        return "~2-3 minutes"


def generate_local_insights(analysis: Dict[str, Any], lang: str = 'fr', 
                           model: str = 'llama3.2:3b',
                           timeout: Optional[int] = None) -> Dict[str, Any]:
    """
    Génère des insights avec Ollama
    CORRECTION : Meilleure détection de timeout + remplissage champs vides
    """
    try:
        # Timeout automatique si non spécifié
        if timeout is None:
            timeout = get_model_timeout(model)
        
        print(f"DEBUG - Modèle: {model}, Timeout: {timeout}s")
        
        # Préparer statistiques (COURT)
        stats_text = ""
        if 'numeric_stats' in analysis and not analysis['numeric_stats'].empty:
            stats_text = f"Stats:\n{analysis['numeric_stats'].to_string()[:300]}"
        
        lang_instruction = "en français" if lang == 'fr' else "in English"
        
        # Résumé COURT
        stats_summary = f"""
Dataset: {analysis['shape'][0]} rows, {analysis['shape'][1]} cols
Numeric: {len(analysis['numeric_cols'])} | Categorical: {len(analysis['categorical_cols'])}
{stats_text}
"""
        
        # Prompt TRÈS COURT (important pour performance)
        prompt = f"""Quick analysis {lang_instruction}. JSON only (no text, no markdown):

{stats_summary}

{{
  "resume_executif": "2 sentences",
  "tendances_principales": ["trend1", "trend2", "trend3"],
  "insights": [
    {{"titre": "Title1", "description": "Brief explanation"}},
    {{"titre": "Title2", "description": "Brief explanation"}}
  ],
  "anomalies": ["anomaly or 'None'"],
  "recommandations": [
    {{"action": "Action1", "justification": "why"}},
    {{"action": "Action2", "justification": "why"}}
  ],
  "conclusion": "1-2 sentences"
}}"""
        
        # Options optimisées pour RAPIDITÉ
        options = {
            "temperature": 0.7,
            "num_predict": 1200,  # Réduit pour plus de rapidité
            "top_k": 40,
            "top_p": 0.9,
            "num_ctx": 2048
        }
        
        # Appel Ollama
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": options
            },
            timeout=timeout
        )
        
        if response.status_code != 200:
            raise Exception(f"Ollama status {response.status_code}: {response.text[:200]}")
        
        result = response.json()
        text = result.get('response', '{}').strip()
        
        print(f"DEBUG - Réponse reçue: {len(text)} caractères")
        
        # Nettoyer JSON
        text = text.replace('```json', '').replace('```', '').strip()
        
        # Parser
        insights = json.loads(text)
        
        # CORRECTION : Validation ET remplissage si vide
        required_fields = {
            'resume_executif': f"Analyse de {analysis['shape'][0]} observations sur {analysis['shape'][1]} variables" if lang == 'fr' else f"Analysis of {analysis['shape'][0]} observations across {analysis['shape'][1]} variables",
            'tendances_principales': [
                f"Dataset de {analysis['shape'][0]} lignes" if lang == 'fr' else f"Dataset with {analysis['shape'][0]} rows",
                f"{len(analysis['numeric_cols'])} variables numériques" if lang == 'fr' else f"{len(analysis['numeric_cols'])} numeric variables",
                f"{len(analysis['categorical_cols'])} variables catégorielles" if lang == 'fr' else f"{len(analysis['categorical_cols'])} categorical variables"
            ],
            'insights': [
                {
                    "titre": "Aperçu des données" if lang == 'fr' else "Data Overview",
                    "description": f"Le dataset contient {analysis['shape'][1]} variables analysées" if lang == 'fr' else f"Dataset contains {analysis['shape'][1]} variables analyzed"
                }
            ],
            'anomalies': ["Aucune anomalie majeure détectée" if lang == 'fr' else "No major anomalies detected"],
            'recommandations': [
                {
                    "action": "Vérification des données" if lang == 'fr' else "Data verification",
                    "justification": "Toujours recommandé avant analyse finale" if lang == 'fr' else "Always recommended before final analysis"
                }
            ],
            'conclusion': "Analyse complétée avec succès" if lang == 'fr' else "Analysis completed successfully"
        }
        
        # Remplir les champs vides
        for field, default_value in required_fields.items():
            if field not in insights or not insights[field]:
                print(f"DEBUG - Champ vide/manquant: {field}, remplissage avec valeur par défaut")
                insights[field] = default_value
            # Vérifier si liste vide
            elif isinstance(insights[field], list) and len(insights[field]) == 0:
                print(f"DEBUG - Liste vide: {field}, remplissage")
                insights[field] = default_value
        
        print("DEBUG - Insights validés et complétés")
        return insights
        
    except requests.exceptions.ConnectionError:
        raise Exception(
            "🔌 Ollama n'est pas lancé. Démarrez: ollama serve" 
            if lang == 'fr' 
            else "🔌 Ollama not running"
        )
    
    except requests.exceptions.Timeout:
        time_est = estimate_generation_time(model)
        raise Exception(
            f"⏰ Timeout après {timeout}s.\n"
            f"Modèle '{model}' estimé à: {time_est}\n\n"
            f"Solutions:\n"
            f"• Réessayez (la génération peut avoir réussi en arrière-plan)\n"
            f"• Utilisez llama3.2:3b si disponible\n"
            f"• Relancez Ollama: ollama serve"
            if lang == 'fr'
            else f"⏰ Timeout after {timeout}s. Try llama3.2:3b"
        )
    
    except json.JSONDecodeError as e:
        print(f"DEBUG - Erreur JSON: {e}")
        print(f"DEBUG - Texte reçu: {text[:500] if 'text' in locals() else 'N/A'}")
        raise Exception(
            f"📄 Réponse JSON invalide. Le modèle '{model}' n'a pas retourné du JSON valide.\n"
            f"Essayez un autre modèle (llama3.2:3b recommandé)."
            if lang == 'fr' 
            else f"📄 Invalid JSON from model '{model}'"
        )
    
    except Exception as e:
        print(f"DEBUG - Erreur générale: {type(e).__name__}: {e}")
        raise Exception(f"❌ Erreur: {str(e)}")


def test_ollama_connection() -> Tuple[bool, str]:
    """Test la connexion Ollama"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=3)
        
        if response.status_code != 200:
            return False, f"Status {response.status_code}"
        
        data = response.json()
        models = data.get('models', [])
        
        if not models:
            return True, "✅ Ollama OK mais aucun modèle"
        
        count = len(models)
        names = ', '.join([m.get('name', '?')[:20] for m in models[:3]])
        
        return True, f"✅ {count} modèle(s): {names}"
    except:
        return False, "❌ Ollama non connecté"


def get_recommended_models() -> List[Dict[str, str]]:
    """Liste des modèles recommandés"""
    return [
        {
            "name": "llama3.2:1b",
            "size": "1.3 GB",
            "speed": "⚡ 30-60s",
            "description": "Le plus rapide"
        },
        {
            "name": "llama3.2:3b",
            "size": "2.0 GB",
            "speed": "🚀 1-2 min",
            "description": "⭐ RECOMMANDÉ"
        },
        {
            "name": "mistral:7b",
            "size": "4.1 GB",
            "speed": "🐌 3-5 min",
            "description": "Qualité mais LENT"
        },
        {
            "name": "mistral:latest",
            "size": "~4 GB",
            "speed": "🐌 3-5 min",
            "description": "Mistral latest (LENT)"
        }
    ]


def format_model_name(raw_name: str) -> str:
    """Formatte un nom de modèle"""
    parts = raw_name.split(':')
    
    if len(parts) >= 2:
        base = parts[0].replace('llama', 'Llama').replace('mistral', 'Mistral')
        version = parts[1].split('-')[0]
        return f"{base} ({version})"
    
    return raw_name


def get_model_info(model_name: str) -> Optional[Dict[str, Any]]:
    """Obtient les infos d'un modèle"""
    try:
        response = requests.post(
            "http://localhost:11434/api/show",
            json={"name": model_name},
            timeout=5
        )
        return response.json() if response.status_code == 200 else None
    except:
        return None


def pull_model(model_name: str) -> Tuple[bool, str]:
    """Télécharge un modèle"""
    try:
        response = requests.post(
            "http://localhost:11434/api/pull",
            json={"name": model_name},
            stream=True,
            timeout=10
        )
        return (True, f"✅ Téléchargement démarré") if response.status_code == 200 else (False, f"❌ Erreur")
    except Exception as e:
        return False, f"❌ {str(e)}"