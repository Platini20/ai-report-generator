"""
Module d'analyse statistique des données
Version améliorée avec analyses détaillées
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List


def analyze_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Analyse complète du dataframe
    
    Args:
        df: DataFrame pandas
        
    Returns:
        dict: Dictionnaire contenant toutes les analyses
    """
    analysis = {}
    
    # ==========================================
    # 1. INFORMATIONS DE BASE
    # ==========================================
    analysis['shape'] = df.shape
    analysis['columns'] = list(df.columns)
    analysis['dtypes'] = df.dtypes.astype(str).to_dict()
    
    # Identifier les types de colonnes
    analysis['numeric_cols'] = list(df.select_dtypes(include=['number']).columns)
    analysis['categorical_cols'] = list(df.select_dtypes(include=['object', 'category']).columns)
    analysis['datetime_cols'] = list(df.select_dtypes(include=['datetime64']).columns)
    analysis['boolean_cols'] = list(df.select_dtypes(include=['bool']).columns)
    
    # ==========================================
    # 2. STATISTIQUES NUMÉRIQUES
    # ==========================================
    if analysis['numeric_cols']:
        analysis['numeric_stats'] = df[analysis['numeric_cols']].describe()
        
        # Statistiques supplémentaires
        analysis['numeric_summary'] = {}
        for col in analysis['numeric_cols']:
            try:
                data = df[col].dropna()
                
                if len(data) > 0:
                    analysis['numeric_summary'][col] = {
                        'count': int(data.count()),
                        'mean': float(data.mean()),
                        'median': float(data.median()),
                        'std': float(data.std()),
                        'min': float(data.min()),
                        'max': float(data.max()),
                        'q1': float(data.quantile(0.25)),
                        'q3': float(data.quantile(0.75)),
                        'skewness': float(data.skew()),
                        'kurtosis': float(data.kurtosis()),
                        'missing': int(df[col].isnull().sum()),
                        'missing_pct': float((df[col].isnull().sum() / len(df)) * 100)
                    }
            except Exception as e:
                print(f"Error analyzing {col}: {e}")
    else:
        analysis['numeric_stats'] = pd.DataFrame()
        analysis['numeric_summary'] = {}
    
    # ==========================================
    # 3. DISTRIBUTION DES CATÉGORIES
    # ==========================================
    analysis['category_dist'] = {}
    analysis['categorical_summary'] = {}
    
    for col in analysis['categorical_cols'][:10]:  # Limiter aux 10 premières
        try:
            # Distribution
            value_counts = df[col].value_counts().head(10)
            analysis['category_dist'][col] = value_counts.to_dict()
            
            # Résumé
            analysis['categorical_summary'][col] = {
                'unique_count': int(df[col].nunique()),
                'most_common': str(df[col].mode()[0]) if len(df[col].mode()) > 0 else None,
                'most_common_freq': int(df[col].value_counts().iloc[0]) if len(df[col]) > 0 else 0,
                'missing': int(df[col].isnull().sum()),
                'missing_pct': float((df[col].isnull().sum() / len(df)) * 100),
                'top_values': [(str(k), int(v)) for k, v in value_counts.head(5).items()]
            }
        except Exception as e:
            print(f"Error analyzing category {col}: {e}")
    
    # ==========================================
    # 4. VALEURS MANQUANTES GLOBALES
    # ==========================================
    missing_counts = df.isnull().sum()
    analysis['missing_values'] = {
        col: {
            'count': int(count),
            'percentage': float((count / len(df)) * 100)
        }
        for col, count in missing_counts.items() if count > 0
    }
    
    # ==========================================
    # 5. CORRÉLATIONS (si > 2 colonnes numériques)
    # ==========================================
    if len(analysis['numeric_cols']) >= 2:
        try:
            corr_matrix = df[analysis['numeric_cols']].corr()
            
            # Trouver les corrélations les plus fortes
            correlations = []
            for i in range(len(corr_matrix.columns)):
                for j in range(i + 1, len(corr_matrix.columns)):
                    col1 = corr_matrix.columns[i]
                    col2 = corr_matrix.columns[j]
                    corr_val = corr_matrix.iloc[i, j]
                    
                    if not pd.isna(corr_val):
                        correlations.append({
                            'col1': col1,
                            'col2': col2,
                            'correlation': float(corr_val)
                        })
            
            # Trier par valeur absolue
            correlations.sort(key=lambda x: abs(x['correlation']), reverse=True)
            analysis['top_correlations'] = correlations[:10]
            
        except Exception as e:
            print(f"Error computing correlations: {e}")
            analysis['top_correlations'] = []
    else:
        analysis['top_correlations'] = []
    
    # ==========================================
    # 6. DÉTECTION D'OUTLIERS (IQR method)
    # ==========================================
    analysis['outliers'] = {}
    
    for col in analysis['numeric_cols'][:20]:  # Limiter pour performance
        try:
            data = df[col].dropna()
            
            if len(data) > 0:
                Q1 = data.quantile(0.25)
                Q3 = data.quantile(0.75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)][col]
                
                if len(outliers) > 0:
                    analysis['outliers'][col] = {
                        'count': int(len(outliers)),
                        'percentage': float((len(outliers) / len(df)) * 100),
                        'lower_bound': float(lower_bound),
                        'upper_bound': float(upper_bound)
                    }
        except Exception as e:
            print(f"Error detecting outliers in {col}: {e}")
    
    # ==========================================
    # 7. UNICITÉ DES COLONNES
    # ==========================================
    analysis['column_uniqueness'] = {}
    
    for col in df.columns[:30]:  # Limiter pour performance
        try:
            unique_count = df[col].nunique()
            total_count = len(df)
            
            analysis['column_uniqueness'][col] = {
                'unique_count': int(unique_count),
                'uniqueness_ratio': float(unique_count / total_count if total_count > 0 else 0),
                'is_unique': bool(unique_count == total_count),
                'is_constant': bool(unique_count == 1)
            }
        except Exception as e:
            print(f"Error analyzing uniqueness of {col}: {e}")
    
    # ==========================================
    # 8. MÉTADONNÉES
    # ==========================================
    analysis['metadata'] = {
        'total_rows': int(len(df)),
        'total_columns': int(len(df.columns)),
        'memory_usage_mb': float(df.memory_usage(deep=True).sum() / (1024 * 1024)),
        'numeric_columns_count': len(analysis['numeric_cols']),
        'categorical_columns_count': len(analysis['categorical_cols']),
        'datetime_columns_count': len(analysis['datetime_cols']),
        'boolean_columns_count': len(analysis['boolean_cols']),
        'total_missing_values': int(df.isnull().sum().sum()),
        'missing_values_percentage': float((df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100)
    }
    
    return analysis


def get_column_recommendations(df: pd.DataFrame, analysis: Dict[str, Any]) -> List[str]:
    """
    Génère des recommandations basées sur l'analyse
    
    Args:
        df: DataFrame
        analysis: Résultat de analyze_dataframe()
        
    Returns:
        list: Liste de recommandations
    """
    recommendations = []
    
    # Colonnes constantes
    constant_cols = [
        col for col, info in analysis['column_uniqueness'].items() 
        if info.get('is_constant', False)
    ]
    if constant_cols:
        recommendations.append(
            f"⚠️ {len(constant_cols)} colonne(s) constante(s) détectée(s): {', '.join(constant_cols[:3])}. "
            "Envisagez de les supprimer."
        )
    
    # Colonnes avec beaucoup de valeurs manquantes
    high_missing = [
        col for col, info in analysis['missing_values'].items()
        if info['percentage'] > 50
    ]
    if high_missing:
        recommendations.append(
            f"⚠️ {len(high_missing)} colonne(s) avec >50% de valeurs manquantes: {', '.join(high_missing[:3])}"
        )
    
    # Outliers significatifs
    high_outliers = [
        col for col, info in analysis['outliers'].items()
        if info['percentage'] > 5
    ]
    if high_outliers:
        recommendations.append(
            f"📊 {len(high_outliers)} colonne(s) avec >5% d'outliers: {', '.join(high_outliers[:3])}"
        )
    
    # Corrélations fortes
    if analysis['top_correlations']:
        strong_corr = [c for c in analysis['top_correlations'] if abs(c['correlation']) > 0.9]
        if strong_corr:
            recommendations.append(
                f"🔗 {len(strong_corr)} paire(s) de colonnes fortement corrélées (>0.9) détectée(s). "
                "Possibilité de redondance."
            )
    
    # Cardinalité élevée
    high_cardinality = [
        col for col, info in analysis['categorical_summary'].items()
        if info['unique_count'] > len(df) * 0.9
    ]
    if high_cardinality:
        recommendations.append(
            f"🏷️ {len(high_cardinality)} colonne(s) catégorielle(s) avec très haute cardinalité: "
            f"{', '.join(high_cardinality[:3])}"
        )
    
    return recommendations if recommendations else ["✅ Aucune anomalie majeure détectée"]