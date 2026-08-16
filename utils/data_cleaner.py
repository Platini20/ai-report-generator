"""
Module de nettoyage et prétraitement des données
SEUIL QUASI-VIDE : ≥90% 
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any, List


def clean_and_preprocess(df: pd.DataFrame, lang: str = 'fr') -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Analyse les données et signale les problèmes SANS supprimer
    ✅ SEUIL QUASI-VIDE : ≥90% 
    
    Args:
        df: DataFrame pandas original
        lang: Langue ('fr' ou 'en')
        
    Returns:
        tuple: (df_cleaned, cleaning_report)
    """
    
    # Initialiser le rapport
    cleaning_report = {
        'original_shape': df.shape,
        'cleaned_shape': df.shape,  # Identique car pas de suppression
        'removed_rows': 0,
        'removed_cols': [],
        'empty_cols': [],
        'quasi_empty_cols': [],  # ✅ SEUIL ≥90%
        'duplicate_rows': 0,
        'missing_values': {},
        'recommendations': [],
        'anomalies_detected': [],
        'warnings': [],
        
        # Compatibilité app.py
        'dropped_empty_columns': [],
        'dropped_duplicate_rows': 0,
        'converted_to_numeric': [],
        'missing_values_after': {}
    }
    
    df_cleaned = df.copy()
    
    # Traductions
    messages = {
        'fr': {
            'empty_detected': "🔍 {} colonne(s) complètement vide(s) détectée(s): {}",
            'quasi_empty': "⚠️ {} colonne(s) quasi-vides (≥90%): {}",
            'duplicates': "🔄 {} ligne(s) dupliquée(s) détectée(s)",
            'missing_top': "📊 Colonnes avec le plus de valeurs manquantes: {}",
            'converted': "🔢 {} colonne(s) convertie(s) en numérique: {}",
            'high_missing': "⚠️ {} colonne(s) avec >50% de valeurs manquantes: {}",
        },
        'en': {
            'empty_detected': "🔍 {} completely empty column(s) detected: {}",
            'quasi_empty': "⚠️ {} quasi-empty column(s) (≥90%): {}",
            'duplicates': "🔄 {} duplicate row(s) detected",
            'missing_top': "📊 Columns with most missing values: {}",
            'converted': "🔢 {} column(s) converted to numeric: {}",
            'high_missing': "⚠️ {} column(s) with >50% missing values: {}",
        }
    }
    
    msg = messages.get(lang, messages['fr'])
    
    # ==========================================
    # 1. NETTOYER LES NOMS DE COLONNES (OK)
    # ==========================================
    df_cleaned.columns = df_cleaned.columns.str.strip()
    
    # ==========================================
    # 2. DÉTECTER LES COLONNES COMPLÈTEMENT VIDES
    # ==========================================
    empty_cols = df_cleaned.columns[df_cleaned.isnull().all()].tolist()
    
    if empty_cols:
        cleaning_report['empty_cols'] = empty_cols
        cleaning_report['anomalies_detected'].append({
            'type': 'empty_columns',
            'severity': 'warning',
            'columns': empty_cols,
            'count': len(empty_cols)
        })
        
        cols_display = ', '.join(map(str, empty_cols[:5]))
        if len(empty_cols) > 5:
            cols_display += f'... (+{len(empty_cols)-5})'
        
        cleaning_report['warnings'].append(
            msg['empty_detected'].format(len(empty_cols), cols_display)
        )
    
    # ==========================================
    # 3. DÉTECTER LES COLONNES QUASI-VIDES (≥90%)
    # ==========================================
    missing_pct = (df_cleaned.isnull().sum() / len(df_cleaned) * 100)
    # ✅ [90%, 100%[ uniquement — les colonnes 100% vides sont déjà comptées
    # dans empty_cols, on évite qu'une même colonne apparaisse dans les deux.
    quasi_empty = missing_pct[(missing_pct >= 90) & (missing_pct < 100)].index.tolist()
    
    if quasi_empty:
        cleaning_report['quasi_empty_cols'] = quasi_empty
        cleaning_report['anomalies_detected'].append({
            'type': 'quasi_empty_columns',
            'severity': 'warning',
            'columns': quasi_empty,
            'count': len(quasi_empty)
        })
        
        cols_display = ', '.join(map(str, quasi_empty[:5]))
        if len(quasi_empty) > 5:
            cols_display += f'... (+{len(quasi_empty)-5})'
        
        cleaning_report['warnings'].append(
            msg['quasi_empty'].format(len(quasi_empty), cols_display)
        )
    
    # ==========================================
    # 4. DÉTECTER LES LIGNES COMPLÈTEMENT VIDES
    # ==========================================
    empty_rows = df_cleaned.isnull().all(axis=1).sum()
    
    if empty_rows > 0:
        cleaning_report['anomalies_detected'].append({
            'type': 'empty_rows',
            'severity': 'info',
            'count': int(empty_rows),
            'percentage': float((empty_rows / len(df_cleaned)) * 100)
        })
    
    # ==========================================
    # 5. DÉTECTER LES DOUBLONS
    # ==========================================
    duplicates = df_cleaned.duplicated().sum()
    
    if duplicates > 0:
        cleaning_report['duplicate_rows'] = duplicates
        cleaning_report['anomalies_detected'].append({
            'type': 'duplicates',
            'severity': 'warning',
            'count': int(duplicates),
            'percentage': float((duplicates / len(df_cleaned)) * 100)
        })
        
        cleaning_report['warnings'].append(
            msg['duplicates'].format(duplicates)
        )
    
    # ==========================================
    # 6. CONVERTIR LES COLONNES NUMÉRIQUES (OK)
    # ==========================================
    converted_cols = []
    
    for col in df_cleaned.select_dtypes(include=['object']).columns:
        try:
            converted = pd.to_numeric(df_cleaned[col], errors='coerce')
            
            if converted.notna().sum() / len(df_cleaned) > 0.5:
                df_cleaned[col] = converted
                converted_cols.append(col)
        except:
            pass
    
    if converted_cols:
        cleaning_report['converted_to_numeric'] = converted_cols
        
        cols_display = ', '.join(map(str, converted_cols[:5]))
        if len(converted_cols) > 5:
            cols_display += f'... (+{len(converted_cols)-5})'
        
        cleaning_report['recommendations'].append(
            msg['converted'].format(len(converted_cols), cols_display)
        )
    
    # ==========================================
    # 7. ANALYSER LES VALEURS MANQUANTES
    # ==========================================
    missing_info = {}
    missing_info_after = {}
    high_missing_cols = []
    
    for col in df_cleaned.columns:
        missing_count = df_cleaned[col].isnull().sum()
        
        if missing_count > 0:
            missing_pct = (missing_count / len(df_cleaned)) * 100
            
            missing_info[col] = {
                'count': int(missing_count),
                'percentage': float(missing_pct)
            }
            
            missing_info_after[col] = int(missing_count)
            
            # Identifier colonnes avec >50% manquant
            if missing_pct > 50:
                high_missing_cols.append((col, missing_pct))
    
    cleaning_report['missing_values'] = missing_info
    cleaning_report['missing_values_after'] = missing_info_after
    
    # Signaler colonnes avec beaucoup de valeurs manquantes
    if high_missing_cols:
        cleaning_report['anomalies_detected'].append({
            'type': 'high_missing_values',
            'severity': 'warning',
            'columns': [(col, pct) for col, pct in high_missing_cols],
            'count': len(high_missing_cols)
        })
        
        cols_display = ', '.join([f"{col} ({pct:.1f}%)" for col, pct in high_missing_cols[:3]])
        if len(high_missing_cols) > 3:
            cols_display += f'... (+{len(high_missing_cols)-3})'
        
        cleaning_report['warnings'].append(
            msg['high_missing'].format(len(high_missing_cols), cols_display)
        )
    
    # Top 3 des colonnes avec valeurs manquantes
    if missing_info:
        top_missing = sorted(
            missing_info.items(), 
            key=lambda x: x[1]['percentage'], 
            reverse=True
        )[:3]
        
        missing_summary = ', '.join([
            f"{col} ({info['percentage']:.1f}%)" 
            for col, info in top_missing
        ])
        
        cleaning_report['recommendations'].append(
            msg['missing_top'].format(missing_summary)
        )
    
    # ==========================================
    # 8. NETTOYER LES ESPACES (OK)
    # ==========================================
    for col in df_cleaned.select_dtypes(include=['object']).columns:
        try:
            df_cleaned[col] = df_cleaned[col].str.strip()
        except:
            pass
    
    # ==========================================
    # 9. FINALISER LE RAPPORT
    
    return df_cleaned, cleaning_report


def get_data_quality_score(cleaning_report: Dict[str, Any]) -> float:
    """Calcule un score de qualité des données (0-100)"""
    score = 100.0
    
    # Pénalités pour colonnes vides
    empty_cols = cleaning_report.get('empty_cols', [])
    if empty_cols:
        score -= min(len(empty_cols) * 10, 30)
    
    # Pénalités pour colonnes quasi-vides (≥90%)
    quasi_empty = cleaning_report.get('quasi_empty_cols', [])
    if quasi_empty:
        score -= min(len(quasi_empty) * 5, 20)
    
    # Pénalités pour doublons
    duplicate_rows = cleaning_report.get('duplicate_rows', 0)
    original_rows = cleaning_report.get('original_shape', (1, 1))[0]
    
    if duplicate_rows > 0 and original_rows > 0:
        dup_penalty = min((duplicate_rows / original_rows) * 100, 15)
        score -= dup_penalty
    
    # Pénalités pour valeurs manquantes
    missing_values = cleaning_report.get('missing_values', {})
    if missing_values:
        avg_missing = np.mean([
            info['percentage'] 
            for info in missing_values.values()
        ])
        score -= min(avg_missing / 2, 25)
    
    return max(0.0, min(100.0, score))


def get_columns_to_exclude_from_viz(cleaning_report: Dict[str, Any]) -> List[str]:
    """
    ✅ Retourne les colonnes à exclure des visualisations
    
    Args:
        cleaning_report: Rapport de nettoyage
        
    Returns:
        list: Colonnes à exclure (vides + quasi-vides ≥90%)
    """
    exclude = []
    
    # Colonnes vides
    exclude.extend(cleaning_report.get('empty_cols', []))
    
    # Colonnes quasi-vides (≥90%)
    exclude.extend(cleaning_report.get('quasi_empty_cols', []))
    
    return list(set(exclude))


def get_detailed_anomaly_report(cleaning_report: Dict[str, Any], lang: str = 'fr') -> Dict[str, Any]:
    """
    ✅ Génère un rapport détaillé des anomalies pour l'IA
    """
    report = {
        'summary': {
            'total_anomalies': len(cleaning_report.get('anomalies_detected', [])),
            'warnings_count': len(cleaning_report.get('warnings', [])),
            'quality_score': get_data_quality_score(cleaning_report)
        },
        'empty_columns': {
            'count': len(cleaning_report.get('empty_cols', [])),
            'columns': cleaning_report.get('empty_cols', [])
        },
        'quasi_empty_columns': {
            'count': len(cleaning_report.get('quasi_empty_cols', [])),
            'columns': cleaning_report.get('quasi_empty_cols', [])
        },
        'duplicates': {
            'count': cleaning_report.get('duplicate_rows', 0),
            'percentage': (cleaning_report.get('duplicate_rows', 0) / 
                          cleaning_report.get('original_shape', (1, 1))[0] * 100)
        },
        'high_missing_values': []
    }
    
    # Colonnes avec >50% et <90% valeurs manquantes uniquement — les colonnes
    # ≥90% sont déjà comptées dans empty_columns / quasi_empty_columns,
    # on évite qu'une même colonne apparaisse dans plusieurs catégories.
    for col, info in cleaning_report.get('missing_values', {}).items():
        if 50 < info['percentage'] < 90:
            report['high_missing_values'].append({
                'column': col,
                'percentage': info['percentage']
            })
    
    return report
