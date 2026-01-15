"""
Module de création des visualisations avec Matplotlib
VERSION INTELLIGENTE : Exclut automatiquement colonnes vides/quasi-vides (≥90%)
"""

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np
from typing import Dict, Tuple, List, Any, Optional

# Configuration du style
sns.set_style("whitegrid")
plt.rcParams['figure.facecolor'] = 'white'
plt.rcParams['axes.facecolor'] = 'white'


def classify_numeric_column(df: pd.DataFrame, col: str) -> str:
    """
    Classifie une colonne numérique selon son type réel
    
    Args:
        df: DataFrame
        col: Nom de la colonne
        
    Returns:
        str: 'continuous', 'discrete', 'binary', 'ordinal'
    """
    unique_count = df[col].nunique()
    total_count = len(df[col].dropna())
    
    if total_count == 0:
        return 'empty'
    
    variety_ratio = unique_count / total_count if total_count > 0 else 0
    
    # Binaire (0/1, True/False, etc.)
    if unique_count == 2:
        return 'binary'
    
    # Discrète (peu de valeurs, souvent des catégories encodées)
    elif unique_count <= 5:
        return 'discrete'
    
    # Continue (beaucoup de valeurs différentes OU ratio de variété élevé)
    elif variety_ratio > 0.3 or unique_count > 15:
        return 'continuous'
    
    # Ordinale/discrète par défaut
    else:
        return 'discrete'


def filter_useful_columns(cols: List[str], df: pd.DataFrame, 
                         exclude_cols: Optional[List[str]] = None) -> List[str]:
    """
    Filtre les colonnes utiles en excluant les problématiques
    ✅ Paramètre exclude_cols pour colonnes vides/quasi-vides
    """
    if exclude_cols is None:
        exclude_cols = []
    
    ignored_keywords = ['id', 'index', 'key', '_id', 'uuid', 'guid', 'unnamed']
    useful = []
    
    for col in cols:
        # ✅ 1. EXCLURE LES COLONNES VIDES/QUASI-VIDES
        if col in exclude_cols:
            continue
        
        col_lower = str(col).lower()
        
        # Ignorer les IDs
        is_id = any(keyword in col_lower for keyword in ignored_keywords)
        if is_id:
            continue
        
        # Vérifier la variance (pour colonnes numériques)
        if col in df.select_dtypes(include=[np.number]).columns:
            try:
                variance = df[col].var()
                if variance == 0 or pd.isna(variance):
                    continue
            except:
                pass
        
        useful.append(col)
    
    return useful if useful else []


def create_visualizations(df: pd.DataFrame, lang: str = 'fr',
                         exclude_cols: Optional[List[str]] = None) -> Dict[str, Tuple[plt.Figure, str]]:
    """
    Crée toutes les visualisations en excluant colonnes vides/quasi-vides
    
    Args:
        df: DataFrame pandas
        lang: Langue ('fr' ou 'en')
        exclude_cols: ✅ NOUVEAU - Liste de colonnes à exclure (vides, quasi-vides ≥90%)
        
    Returns:
        dict: {nom: (figure, interprétation)}
    """
    figs = {}
    
    # Identifier colonnes utiles (en excluant les problématiques)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # ✅ PASSER exclude_cols au filtre
    useful_numeric = filter_useful_columns(numeric_cols, df, exclude_cols)
    useful_categorical = filter_useful_columns(categorical_cols, df, exclude_cols)
    
    # Si pas assez de colonnes après filtrage, signaler
    if not useful_numeric and not useful_categorical:
        print(f"⚠️ Warning: No useful columns after filtering (excluded {len(exclude_cols or [])} columns)")
        return figs
    
    # Classifier les colonnes numériques
    numeric_types = {col: classify_numeric_column(df, col) for col in useful_numeric}
    
    # Séparer par type
    continuous_cols = [c for c, t in numeric_types.items() if t == 'continuous']
    discrete_cols = [c for c, t in numeric_types.items() if t in ['discrete', 'ordinal']]
    binary_cols = [c for c, t in numeric_types.items() if t == 'binary']
    
    # Traductions
    t = _get_translations(lang)
    
    # 1. Distribution des variables CONTINUES (Histogrammes)
    if continuous_cols:
        fig, interp = _create_distributions(df, continuous_cols[:4], t)
        if fig:
            figs['continuous_distributions'] = (fig, interp)
    
    # 2. Distribution des variables DISCRÈTES (Bar charts)
    if discrete_cols:
        fig, interp = _create_discrete_distributions(df, discrete_cols[:4], t)
        if fig:
            figs['discrete_distributions'] = (fig, interp)
    
    # 3. Boxplots - Mixte continues/discrètes si besoin
    boxplot_cols = continuous_cols[:6] if continuous_cols else []
    
    # Si pas assez de continues, ajouter des discrètes
    if len(boxplot_cols) < 2 and discrete_cols:
        discrete_sorted = sorted(discrete_cols, key=lambda c: df[c].nunique(), reverse=True)
        needed = min(6 - len(boxplot_cols), len(discrete_sorted))
        boxplot_cols.extend(discrete_sorted[:needed])
    
    if boxplot_cols and len(boxplot_cols) >= 1:
        fig, interp = _create_boxplots(df, boxplot_cols, t)
        if fig:
            figs['outlier_detection'] = (fig, interp)
    
    # 4. Matrice de corrélation (seulement continues)
    if len(continuous_cols) >= 2:
        fig, interp = _create_correlation_matrix(df, continuous_cols[:10], t)
        if fig:
            figs['correlation_matrix'] = (fig, interp)
    
    # 5. Analyse catégorielle vs numérique
    if useful_categorical and useful_numeric:
        fig, interp = _create_categorical_analysis(df, useful_categorical[0], useful_numeric[0], t)
        if fig:
            figs['categorical_analysis'] = (fig, interp)
    
    # 6. Relation intelligente entre variables
    if len(continuous_cols) >= 2:
        fig, interp = _create_scatter_plot(df, continuous_cols[0], continuous_cols[1], t)
        if fig:
            figs['relationship_scatter'] = (fig, interp)
    
    # 7. Analyse groupée si discrète + continue
    if discrete_cols and continuous_cols:
        fig, interp = _create_grouped_boxplot(df, discrete_cols[0], continuous_cols[0], t)
        if fig:
            figs['grouped_analysis'] = (fig, interp)
    
    # 8. Distribution catégorielle (pie chart)
    if useful_categorical:
        fig, interp = _create_pie_chart(df, useful_categorical[0], t)
        if fig:
            figs['categorical_distribution'] = (fig, interp)
    
    return figs


def _create_distributions(df: pd.DataFrame, cols: List[str], t: Dict) -> Tuple[plt.Figure, str]:
    """Crée les histogrammes pour variables CONTINUES"""
    try:
        n_cols = min(len(cols), 4)
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(t['dist_title_continuous'], fontsize=16, fontweight='bold')
        axes = axes.flatten()
        
        for idx, col in enumerate(cols[:4]):
            if idx >= len(axes):
                break
            
            ax = axes[idx]
            data = df[col].dropna()
            
            if len(data) > 0:
                ax.hist(data, bins=30, color='#667eea', alpha=0.7, edgecolor='black')
                ax.set_title(f'{col}', fontsize=12, fontweight='bold')
                ax.set_xlabel(t['value'], fontsize=10)
                ax.set_ylabel(t['frequency'], fontsize=10)
                ax.grid(True, alpha=0.3)
                
                # Stats
                mean_val = data.mean()
                median_val = data.median()
                ax.axvline(mean_val, color='red', linestyle='--', linewidth=2, label=f'Mean: {mean_val:.2f}')
                ax.axvline(median_val, color='green', linestyle='--', linewidth=2, label=f'Median: {median_val:.2f}')
                ax.legend(fontsize=8)
        
        # Masquer les axes vides
        for idx in range(len(cols), len(axes)):
            axes[idx].set_visible(False)
        
        plt.tight_layout()
        return fig, t['dist_desc_continuous']
        
    except Exception as e:
        print(f"Error creating distributions: {e}")
        return None, ""


def _create_discrete_distributions(df: pd.DataFrame, cols: List[str], t: Dict) -> Tuple[plt.Figure, str]:
    """Crée des bar charts pour variables DISCRÈTES"""
    try:
        n_cols = min(len(cols), 4)
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle(t['dist_title_discrete'], fontsize=16, fontweight='bold')
        axes = axes.flatten()
        
        for idx, col in enumerate(cols[:4]):
            if idx >= len(axes):
                break
            
            ax = axes[idx]
            data = df[col].dropna()
            
            if len(data) > 0:
                value_counts = data.value_counts().sort_index()
                
                bars = ax.bar(range(len(value_counts)), value_counts.values, 
                             color='#764ba2', alpha=0.7, edgecolor='black')
                
                ax.set_xticks(range(len(value_counts)))
                ax.set_xticklabels([f'{v:.1f}' if isinstance(v, float) else str(v) 
                                   for v in value_counts.index], rotation=0)
                ax.set_title(f'{col} ({len(value_counts)} {t["values"]})', fontsize=12, fontweight='bold')
                ax.set_xlabel(t['value'], fontsize=10)
                ax.set_ylabel(t['count'], fontsize=10)
                ax.grid(True, alpha=0.3, axis='y')
                
                # Ajouter les counts sur les barres
                for bar in bars:
                    height = bar.get_height()
                    ax.text(bar.get_x() + bar.get_width()/2., height,
                           f'{int(height)}', ha='center', va='bottom', fontsize=9)
        
        # Masquer les axes vides
        for idx in range(len(cols), len(axes)):
            axes[idx].set_visible(False)
        
        plt.tight_layout()
        return fig, t['dist_desc_discrete']
        
    except Exception as e:
        print(f"Error creating discrete distributions: {e}")
        return None, ""


def _create_boxplots(df: pd.DataFrame, cols: List[str], t: Dict) -> Tuple[plt.Figure, str]:
    """
    Boxplots avec affichage de TOUTES les variables avec outliers
    ✅ PAS DE LIMITE À 3 - Affiche toutes (max 10 pour lisibilité)
    """
    try:
        fig, ax = plt.subplots(figsize=(14, 6))
        
        data_to_plot = []
        labels = []
        outlier_counts = []
        
        for col in cols:
            data = df[col].dropna()
            if len(data) > 0:
                data_to_plot.append(data)
                labels.append(col)
                
                Q1 = data.quantile(0.25)
                Q3 = data.quantile(0.75)
                IQR = Q3 - Q1
                outliers = ((data < Q1 - 1.5*IQR) | (data > Q3 + 1.5*IQR)).sum()
                outlier_counts.append(outliers)
        
        if data_to_plot:
            bp = ax.boxplot(data_to_plot, labels=labels, patch_artist=True)
            
            for patch in bp['boxes']:
                patch.set_facecolor('#667eea')
                patch.set_alpha(0.7)
            
            ax.set_title(t['outlier_title'], fontsize=14, fontweight='bold')
            ax.set_ylabel(t['value'], fontsize=12)
            ax.grid(True, alpha=0.3, axis='y')
            plt.xticks(rotation=45, ha='right')
            
            # ✅ AFFICHER TOUTES LES VARIABLES (limite 10 pour message)
            total_outliers = sum(outlier_counts)
            if total_outliers > 0:
                outlier_data = [(labels[i], outlier_counts[i]) for i in range(len(labels)) if outlier_counts[i] > 0]
                outlier_data_sorted = sorted(outlier_data, key=lambda x: x[1], reverse=True)
                
                # Limite optionnelle à 10 pour éviter message trop long
                if len(outlier_data_sorted) > 10:
                    displayed_vars = [name for name, count in outlier_data_sorted[:10]]
                    remaining = len(outlier_data_sorted) - 10
                    # ✅ CORRIGÉ : Utiliser traduction au lieu de "autres variables" en dur
                    interp = f"{t['outlier_detected']}: {', '.join(displayed_vars)} (+{remaining} {t['more_variables']}). {t['outlier_action']}"
                else:
                    all_vars = [name for name, count in outlier_data_sorted]
                    interp = f"{t['outlier_detected']}: {', '.join(all_vars)}. {t['outlier_action']}"
            else:
                interp = t['no_outliers']
            
            plt.tight_layout()
            return fig, interp
        
        return None, ""
        
    except Exception as e:
        print(f"Error creating boxplots: {e}")
        return None, ""


def _create_correlation_matrix(df: pd.DataFrame, cols: List[str], t: Dict) -> Tuple[plt.Figure, str]:
    """Crée la matrice de corrélation"""
    try:
        fig, ax = plt.subplots(figsize=(12, 10))
        
        corr_matrix = df[cols].corr()
        corr_matrix = corr_matrix.fillna(0)
        
        sns.heatmap(corr_matrix, annot=True, fmt='.2f', cmap='RdBu_r', 
                   center=0, square=True, ax=ax, cbar_kws={'label': t['correlation']},
                   vmin=-1, vmax=1)
        
        ax.set_title(t['corr_title'], fontsize=14, fontweight='bold')
        plt.xticks(rotation=45, ha='right')
        plt.yticks(rotation=0)
        
        # Trouver la corrélation la plus forte (hors diagonale)
        mask = np.triu(np.ones_like(corr_matrix, dtype=bool))
        corr_values = corr_matrix.mask(mask)
        corr_flat = corr_values.values.flatten()
        valid_corrs = corr_flat[~np.isnan(corr_flat) & (np.abs(corr_flat) < 0.9999)]
        
        if len(valid_corrs) > 0:
            max_abs_corr = np.max(np.abs(valid_corrs))
            max_corr_value = valid_corrs[np.abs(valid_corrs) == max_abs_corr][0]
            
            found = False
            for i in range(len(corr_matrix)):
                for j in range(i + 1, len(corr_matrix)):
                    if abs(corr_matrix.iloc[i, j] - max_corr_value) < 0.001:
                        var1 = corr_matrix.index[i]
                        var2 = corr_matrix.columns[j]
                        max_corr = max_corr_value
                        found = True
                        break
                if found:
                    break
            
            if found:
                if abs(max_corr) > 0.7:
                    strength = t['strong']
                elif abs(max_corr) > 0.4:
                    strength = t['moderate']
                else:
                    strength = t['weak']
                
                interp = f"{t['corr_insight']}: {strength} {t['between']} '{var1}' {t['and']} '{var2}' (r={max_corr:.2f})"
            else:
                interp = t['corr_insight']
        else:
            interp = t['corr_insight']
        
        plt.tight_layout()
        return fig, interp
        
    except Exception as e:
        print(f"Error creating correlation matrix: {e}")
        return None, ""


def _create_categorical_analysis(df: pd.DataFrame, cat_col: str, num_col: str, t: Dict) -> Tuple[plt.Figure, str]:
    """Crée un barplot catégorie vs numérique"""
    try:
        fig, ax = plt.subplots(figsize=(12, 6))
        
        grouped = df.groupby(cat_col)[num_col].sum().sort_values(ascending=False).head(10)
        
        bars = ax.bar(range(len(grouped)), grouped.values, color='#667eea', alpha=0.8, edgecolor='black')
        ax.set_xticks(range(len(grouped)))
        ax.set_xticklabels(grouped.index, rotation=45, ha='right')
        ax.set_title(f'{t["top"]} 10 {cat_col} {t["by"]} {num_col}', fontsize=14, fontweight='bold')
        ax.set_ylabel(num_col, fontsize=12)
        ax.grid(True, alpha=0.3, axis='y')
        
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                   f'{height:.0f}', ha='center', va='bottom', fontsize=9)
        
        top_cat = grouped.index[0]
        top_val = grouped.values[0]
        top3_pct = (grouped.head(3).sum() / grouped.sum() * 100)
        
        interp = f"{t['key_finding']}: '{top_cat}' {t['leads_with']} {top_val:.0f}. {t['top3']} {top3_pct:.1f}% {t['of_total']}"
        
        plt.tight_layout()
        return fig, interp
        
    except Exception as e:
        print(f"Error creating categorical analysis: {e}")
        return None, ""


def _create_scatter_plot(df: pd.DataFrame, col1: str, col2: str, t: Dict) -> Tuple[plt.Figure, str]:
    """Crée un scatter plot continues vs continues"""
    try:
        fig, ax = plt.subplots(figsize=(10, 6))
        
        plot_df = df[[col1, col2]].dropna().head(500)
        
        ax.scatter(plot_df[col1], plot_df[col2], alpha=0.6, s=50, color='#667eea', edgecolors='black', linewidth=0.5)
        
        z = np.polyfit(plot_df[col1], plot_df[col2], 1)
        p = np.poly1d(z)
        ax.plot(plot_df[col1].sort_values(), p(plot_df[col1].sort_values()), 
               "r--", linewidth=2, label=f'Trend: y={z[0]:.2f}x+{z[1]:.2f}')
        
        ax.set_xlabel(col1, fontsize=12)
        ax.set_ylabel(col2, fontsize=12)
        ax.set_title(f'{t["relationship"]}: {col1} vs {col2}', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend()
        
        corr = plot_df[col1].corr(plot_df[col2])
        
        if pd.isna(corr) or abs(corr) < 0.001:
            strength = t['weak']
        elif corr > 0.7:
            strength = t['strong_pos']
        elif corr > 0.3:
            strength = t['moderate_pos']
        elif corr > -0.3:
            strength = t['weak']
        elif corr > -0.7:
            strength = t['moderate_neg']
        else:
            strength = t['strong_neg']
        
        interp = f"{strength} {t['correlation'].lower()} (r={corr:.2f}) {t['between']} {col1} {t['and']} {col2}"
        
        plt.tight_layout()
        return fig, interp
        
    except Exception as e:
        print(f"Error creating scatter plot: {e}")
        return None, ""


def _create_grouped_boxplot(df: pd.DataFrame, discrete_col: str, continuous_col: str, t: Dict) -> Tuple[plt.Figure, str]:
    """Crée un boxplot groupé : Variable discrète (X) vs Variable continue (Y)"""
    try:
        fig, ax = plt.subplots(figsize=(12, 6))
        
        data_clean = df[[discrete_col, continuous_col]].dropna()
        
        unique_values = sorted(data_clean[discrete_col].unique())
        if len(unique_values) > 15:
            top_values = data_clean[discrete_col].value_counts().head(15).index
            data_clean = data_clean[data_clean[discrete_col].isin(top_values)]
            unique_values = sorted(data_clean[discrete_col].unique())
        
        positions = range(len(unique_values))
        data_by_group = [data_clean[data_clean[discrete_col] == val][continuous_col].values 
                        for val in unique_values]
        
        bp = ax.boxplot(data_by_group, positions=positions, patch_artist=True,
                       labels=[f'{v:.1f}' if isinstance(v, float) else str(v) for v in unique_values])
        
        for patch in bp['boxes']:
            patch.set_facecolor('#667eea')
            patch.set_alpha(0.6)
        
        ax.set_xlabel(discrete_col, fontsize=12, fontweight='bold')
        ax.set_ylabel(continuous_col, fontsize=12, fontweight='bold')
        ax.set_title(f'{t["grouped_analysis"]}: {continuous_col} {t["by"]} {discrete_col}', 
                    fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        
        if len(unique_values) > 8:
            plt.xticks(rotation=45, ha='right')
        
        means_by_group = [data_clean[data_clean[discrete_col] == val][continuous_col].mean() 
                         for val in unique_values]
        max_mean_idx = np.argmax(means_by_group)
        min_mean_idx = np.argmin(means_by_group)
        
        # ✅ CORRIGÉ : Utiliser traduction au lieu de "moyenne" en dur
        interp = (
            f"{t['grouped_insight']}: "
            f"{t['highest']} {continuous_col} {t['for']} {discrete_col}={unique_values[max_mean_idx]} "
            f"({t['mean_label']}: {means_by_group[max_mean_idx]:.2f}). "
            f"{t['lowest']} {t['for']} {discrete_col}={unique_values[min_mean_idx]} "
            f"({t['mean_label']}: {means_by_group[min_mean_idx]:.2f})."
        )
        
        plt.tight_layout()
        return fig, interp
        
    except Exception as e:
        print(f"Error creating grouped boxplot: {e}")
        return None, ""


def _create_pie_chart(df: pd.DataFrame, col: str, t: Dict) -> Tuple[plt.Figure, str]:
    """Crée un pie chart"""
    try:
        fig, ax = plt.subplots(figsize=(10, 8))
        
        value_counts = df[col].value_counts().head(6)
        colors = ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b', '#fa709a']
        
        wedges, texts, autotexts = ax.pie(value_counts.values, labels=value_counts.index, 
                                           autopct='%1.1f%%', startangle=90,
                                           colors=colors, textprops={'fontsize': 10})
        
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        ax.set_title(f'{t["distribution"]}: {col}', fontsize=14, fontweight='bold')
        
        top_cat = value_counts.index[0]
        top_pct = (value_counts.values[0] / value_counts.sum() * 100)
        
        interp = f"'{top_cat}' {t['dominates']} {top_pct:.1f}% {t['of_dist']}"
        
        plt.tight_layout()
        return fig, interp
        
    except Exception as e:
        print(f"Error creating pie chart: {e}")
        return None, ""


def _get_translations(lang: str) -> Dict[str, str]:
    """Retourne les traductions"""
    translations = {
        'fr': {
            'dist_title_continuous': 'Distribution des Variables Continues',
            'dist_title_discrete': 'Distribution des Variables Discrètes',
            'dist_desc_continuous': 'Histogrammes des variables continues avec moyenne (rouge) et médiane (vert)',
            'dist_desc_discrete': 'Diagrammes en barres des variables discrètes montrant la fréquence de chaque valeur',
            'value': 'Valeur',
            'values': 'valeurs',
            'frequency': 'Fréquence',
            'count': 'Nombre',
            'outlier_title': 'Détection des Valeurs Aberrantes',
            'outlier_detected': 'Valeurs aberrantes détectées dans',
            'outlier_action': 'Investigation recommandée',
            'no_outliers': 'Aucune valeur aberrante significative',
            'corr_title': 'Matrice de Corrélation',
            'correlation': 'Corrélation',
            'corr_insight': 'Corrélation la plus forte',
            'strong': 'forte',
            'moderate': 'modérée',
            'weak': 'faible',
            'between': 'entre',
            'and': 'et',
            'top': 'Top',
            'by': 'par',
            'for': 'pour',
            'key_finding': 'Résultat clé',
            'leads_with': 'domine avec',
            'top3': 'Le top 3 représente',
            'of_total': 'du total',
            'relationship': 'Relation',
            'strong_pos': 'Corrélation positive forte',
            'moderate_pos': 'Corrélation positive modérée',
            'moderate_neg': 'Corrélation négative modérée',
            'strong_neg': 'Corrélation négative forte',
            'distribution': 'Distribution',
            'dominates': 'domine avec',
            'of_dist': 'de la distribution',
            'grouped_analysis': 'Analyse Groupée',
            'grouped_insight': 'Analyse par groupe',
            'highest': 'Valeur maximale de',
            'lowest': 'Valeur minimale',
            'more_variables': 'autres variables',
            'mean_label': 'moyenne'
        },
        'en': {
            'dist_title_continuous': 'Continuous Variables Distribution',
            'dist_title_discrete': 'Discrete Variables Distribution',
            'dist_desc_continuous': 'Histograms of continuous variables with mean (red) and median (green)',
            'dist_desc_discrete': 'Bar charts of discrete variables showing frequency of each value',
            'value': 'Value',
            'values': 'values',
            'frequency': 'Frequency',
            'count': 'Count',
            'outlier_title': 'Outlier Detection',
            'outlier_detected': 'Outliers detected in',
            'outlier_action': 'Investigation recommended',
            'no_outliers': 'No significant outliers',
            'corr_title': 'Correlation Matrix',
            'correlation': 'Correlation',
            'corr_insight': 'Strongest correlation',
            'strong': 'strong',
            'moderate': 'moderate',
            'weak': 'weak',
            'between': 'between',
            'and': 'and',
            'top': 'Top',
            'by': 'by',
            'for': 'for',
            'key_finding': 'Key finding',
            'leads_with': 'leads with',
            'top3': 'Top 3 represent',
            'of_total': 'of total',
            'relationship': 'Relationship',
            'strong_pos': 'Strong positive correlation',
            'moderate_pos': 'Moderate positive correlation',
            'moderate_neg': 'Moderate negative correlation',
            'strong_neg': 'Strong negative correlation',
            'distribution': 'Distribution',
            'dominates': 'dominates with',
            'of_dist': 'of distribution',
            'grouped_analysis': 'Grouped Analysis',
            'grouped_insight': 'Group analysis',
            'highest': 'Highest value of',
            'lowest': 'Lowest value',
            'more_variables': 'more variables',
            'mean_label': 'mean'
        }
    }
    
    return translations.get(lang, translations['fr'])
