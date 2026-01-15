"""
Module de chargement des fichiers de données
Supporte: CSV, Excel, JSON, Parquet
"""

import pandas as pd
import streamlit as st
from typing import Optional


def load_file(uploaded_file) -> Optional[pd.DataFrame]:
    """
    Charge différents types de fichiers
    
    Args:
        uploaded_file: Fichier uploadé via Streamlit
        
    Returns:
        DataFrame pandas ou None en cas d'erreur
    """
    if uploaded_file is None:
        return None
    
    # Obtenir l'extension du fichier
    file_extension = uploaded_file.name.split('.')[-1].lower()
    
    try:
        # Rewind du fichier (important avec Streamlit)
        try:
            uploaded_file.seek(0)
        except:
            pass
        
        # CSV
        if file_extension == 'csv':
            df = pd.read_csv(uploaded_file)
            
        # Excel
        elif file_extension in ['xlsx', 'xls']:
            df = pd.read_excel(uploaded_file, engine='openpyxl' if file_extension == 'xlsx' else None)
            
        # JSON
        elif file_extension == 'json':
            df = pd.read_json(uploaded_file)
            
        # Parquet
        elif file_extension == 'parquet':
            df = pd.read_parquet(uploaded_file)
            
        else:
            st.error(f"❌ Format non supporté: {file_extension}")
            return None
        
        # Vérifications basiques
        if df.empty:
            st.error("❌ Le fichier est vide")
            return None
        
        if len(df.columns) == 0:
            st.error("❌ Aucune colonne détectée")
            return None
        
        return df
        
    except pd.errors.EmptyDataError:
        st.error("❌ Le fichier est vide ou mal formaté")
        return None
        
    except pd.errors.ParserError as e:
        st.error(f"❌ Erreur de parsing: {str(e)}")
        return None
        
    except Exception as e:
        st.error(f"❌ Erreur lors du chargement: {str(e)}")
        return None


def detect_encoding(file_path: str) -> str:
    """
    Détecte l'encodage d'un fichier (utile pour CSV)
    
    Args:
        file_path: Chemin du fichier
        
    Returns:
        str: Encodage détecté (utf-8, latin1, etc.)
    """
    import chardet
    
    try:
        with open(file_path, 'rb') as f:
            result = chardet.detect(f.read())
            return result['encoding']
    except:
        return 'utf-8'  # Fallback


def load_csv_with_options(uploaded_file, sep: str = ',', encoding: str = 'utf-8',
                        decimal: str = '.', thousands: Optional[str] = None) -> Optional[pd.DataFrame]:
    """
    Charge un CSV avec options avancées
    
    Args:
        uploaded_file: Fichier uploadé
        sep: Séparateur (virgule, point-virgule, etc.)
        encoding: Encodage du fichier
        decimal: Caractère décimal
        thousands: Séparateur de milliers
        
    Returns:
        DataFrame ou None
    """
    try:
        df = pd.read_csv(
            uploaded_file,
            sep=sep,
            encoding=encoding,
            decimal=decimal,
            thousands=thousands,
            on_bad_lines='skip'  # Ignore les lignes mal formatées
        )
        return df
    except Exception as e:
        st.error(f"❌ Erreur: {str(e)}")
        return None


def get_file_info(uploaded_file) -> dict:
    """
    Obtient des informations sur le fichier uploadé
    
    Args:
        uploaded_file: Fichier Streamlit
        
    Returns:
        dict: Informations du fichier
    """
    if uploaded_file is None:
        return {}
    
    try:
        return {
            'name': uploaded_file.name,
            'size': uploaded_file.size,
            'size_mb': round(uploaded_file.size / (1024 * 1024), 2),
            'type': uploaded_file.type,
            'extension': uploaded_file.name.split('.')[-1].lower()
        }
    except:
        return {}