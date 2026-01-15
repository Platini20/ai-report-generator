"""
Gestionnaire de configuration persistante
Sauvegarde les paramètres utilisateur (clé API, modèle préféré, etc.)
"""

import os
import pickle
from pathlib import Path
from typing import Optional, Dict, Any
import streamlit as st


# Chemin du fichier de configuration
CONFIG_DIR = Path.home() / ".streamlit"
CONFIG_FILE = CONFIG_DIR / "ai_report_generator_config.pkl"


def ensure_config_dir():
    """Crée le répertoire de config s'il n'existe pas"""
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Warning: Could not create config directory: {e}")


def load_config() -> Dict[str, Any]:
    """
    Charge la configuration sauvegardée
    
    Returns:
        dict: Configuration ou dict vide
    """
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'rb') as f:
                config = pickle.load(f)
                return config if isinstance(config, dict) else {}
    except Exception as e:
        print(f"Error loading config: {e}")
    
    return {}


def save_config(config: Dict[str, Any]):
    """
    Sauvegarde la configuration
    
    Args:
        config: Dictionnaire de configuration
    """
    try:
        ensure_config_dir()
        with open(CONFIG_FILE, 'wb') as f:
            pickle.dump(config, f)
    except Exception as e:
        print(f"Error saving config: {e}")


def get_api_key() -> Optional[str]:
    """
    Récupère la clé API sauvegardée
    
    Essaie d'abord st.secrets (production Streamlit Cloud),
    puis le fichier local (développement)
    
    Returns:
        str: Clé API ou None
    """
    # D'abord essayer st.secrets (Streamlit Cloud)
    try:
        if hasattr(st, 'secrets') and 'anthropic_api_key' in st.secrets:
            return st.secrets['anthropic_api_key']
    except:
        pass
    
    # Sinon essayer le fichier local
    config = load_config()
    return config.get('anthropic_api_key')


def save_api_key(api_key: str):
    """
    Sauvegarde la clé API
    
    Args:
        api_key: Clé API à sauvegarder
    """
    config = load_config()
    config['anthropic_api_key'] = api_key
    save_config(config)


def delete_api_key():
    """Supprime la clé API sauvegardée"""
    config = load_config()
    if 'anthropic_api_key' in config:
        del config['anthropic_api_key']
        save_config(config)


def get_ollama_model() -> Optional[str]:
    """Récupère le modèle Ollama préféré"""
    config = load_config()
    return config.get('ollama_model')


def save_ollama_model(model: str):
    """Sauvegarde le modèle Ollama préféré"""
    config = load_config()
    config['ollama_model'] = model
    save_config(config)


def get_user_preferences() -> Dict[str, Any]:
    """Récupère toutes les préférences utilisateur"""
    config = load_config()
    return config.get('preferences', {})


def save_user_preference(key: str, value: Any):
    """
    Sauvegarde une préférence utilisateur
    
    Args:
        key: Nom de la préférence
        value: Valeur à sauvegarder
    """
    config = load_config()
    if 'preferences' not in config:
        config['preferences'] = {}
    config['preferences'][key] = value
    save_config(config)


def clear_all_config():
    """Supprime toute la configuration"""
    try:
        if CONFIG_FILE.exists():
            CONFIG_FILE.unlink()
    except Exception as e:
        print(f"Error clearing config: {e}")

# Dans config_manager.py, ajouter :
def get_api_key() -> Optional[str]:
    # D'abord essayer st.secrets (production)
    try:
        if 'anthropic_api_key' in st.secrets:
            return st.secrets['anthropic_api_key']
    except:
        pass
    
    # Sinon essayer le fichier local (dev)
    config = load_config()
    return config.get('anthropic_api_key')