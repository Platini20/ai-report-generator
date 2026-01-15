"""
Module d'export en format HTML (imprimable en PDF)
Avec graphiques intégrés en base64
"""

from datetime import datetime
import base64
from io import BytesIO
from typing import Dict, Any, Optional
import matplotlib.pyplot as plt


def fig_to_base64(fig: plt.Figure) -> str:
    """Convertit une figure matplotlib en string base64"""
    buffer = BytesIO()
    fig.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
    buffer.seek(0)
    image_base64 = base64.b64encode(buffer.read()).decode()
    plt.close(fig)
    return f"data:image/png;base64,{image_base64}"


def generate_html_report(df, analysis: Dict[str, Any], ai_insights: Dict[str, Any], 
                        lang: str = 'fr', visualizations: Optional[Dict] = None) -> str:
    """
    Génère un rapport HTML imprimable en PDF avec graphiques intégrés
    
    Args:
        df: DataFrame pandas
        analysis: Dictionnaire d'analyse
        ai_insights: Insights générés
        lang: Langue ('fr' ou 'en')
        visualizations: Dict {nom: (figure, interprétation)} optionnel
        
    Returns:
        str: Code HTML du rapport
    """
    
    # Traductions
    titles = {
        'fr': {
            'report': 'RAPPORT D\'ANALYSE PROFESSIONNEL',
            'summary': 'Résumé Exécutif',
            'overview': 'Vue d\'Ensemble',
            'stats': 'Statistiques Détaillées',
            'visualizations': 'Visualisations & Analyses',
            'trends': 'Tendances Principales',
            'analysis': 'Analyses Approfondies',
            'reco': 'Recommandations Stratégiques',
            'conclusion': 'Conclusion',
            'obs': 'Observations',
            'vars': 'Variables',
            'num': 'Numériques',
            'cat': 'Catégorielles',
            'print_btn': '🖨️ Imprimer / Sauvegarder en PDF',
            'generated': 'Rapport généré automatiquement',
            'powered': 'Propulsé par IA'
        },
        'en': {
            'report': 'PROFESSIONAL ANALYSIS REPORT',
            'summary': 'Executive Summary',
            'overview': 'Overview',
            'stats': 'Detailed Statistics',
            'visualizations': 'Visualizations & Analysis',
            'trends': 'Main Trends',
            'analysis': 'Deep Analysis',
            'reco': 'Strategic Recommendations',
            'conclusion': 'Conclusion',
            'obs': 'Observations',
            'vars': 'Variables',
            'num': 'Numeric',
            'cat': 'Categorical',
            'print_btn': '🖨️ Print / Save as PDF',
            'generated': 'Report generated automatically',
            'powered': 'Powered by AI'
        }
    }
    
    t = titles[lang]
    
    # Début du HTML avec styles améliorés
    html = f"""
<!DOCTYPE html>
<html lang="{lang}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{t['report']}</title>
    <style>
        @media print {{
            .no-print {{ display: none !important; }}
            @page {{ 
                margin: 1.5cm; 
                size: A4;
            }}
            body {{ 
                margin: 0;
                padding: 0;
            }}
            .page-break {{ 
                page-break-before: always; 
            }}
            h2 {{
                page-break-after: avoid;
            }}
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            max-width: 1000px;
            margin: 0 auto;
            padding: 20px;
            color: #2c3e50;
            background: #f8f9fa;
        }}
        
        .container {{
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 3px solid #667eea;
        }}
        
        h1 {{
            color: #667eea;
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 800;
            letter-spacing: -1px;
        }}
        
        .date {{
            color: #7f8c8d;
            font-size: 1.1em;
            font-weight: 500;
        }}
        
        h2 {{
            color: #667eea;
            font-size: 1.8em;
            margin-top: 40px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid #667eea;
            font-weight: 700;
        }}
        
        h3 {{
            color: #764ba2;
            font-size: 1.3em;
            margin-top: 25px;
            margin-bottom: 15px;
            font-weight: 600;
        }}
        
        .stat-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 30px 0;
        }}
        
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 25px;
            border-radius: 12px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            transition: transform 0.3s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        
        .stat-card h3 {{
            margin: 0 0 10px 0;
            font-size: 0.95em;
            opacity: 0.95;
            color: white;
            border: none;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .stat-card p {{
            margin: 0;
            font-size: 2.8em;
            font-weight: 800;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        
        .insight-box {{
            background: linear-gradient(to right, #f8f9fa 0%, #e9ecef 100%);
            border-left: 5px solid #667eea;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .insight-box p {{
            margin: 0;
            line-height: 1.8;
            font-size: 1.05em;
        }}
        
        .recommendation {{
            background: linear-gradient(to right, #f0fdf4 0%, #dcfce7 100%);
            border-left: 5px solid #10b981;
            padding: 20px;
            margin: 20px 0;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        
        .recommendation h3 {{
            color: #059669;
            margin-top: 0;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 25px 0;
            font-size: 0.95em;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }}
        
        th, td {{
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #e5e7eb;
        }}
        
        th {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85em;
            letter-spacing: 0.5px;
        }}
        
        tr:nth-child(even) {{
            background-color: #f8f9fa;
        }}
        
        tr:hover {{
            background-color: #e9ecef;
        }}
        
        .print-button {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            font-size: 1.1em;
            font-weight: 600;
            border-radius: 8px;
            cursor: pointer;
            margin: 20px auto;
            display: block;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            transition: all 0.3s;
        }}
        
        .print-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }}
        
        .visualization {{
            margin: 30px 0;
            text-align: center;
        }}
        
        .visualization img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        
        .viz-interpretation {{
            background: #f8f9fa;
            padding: 15px;
            margin-top: 15px;
            border-radius: 8px;
            font-style: italic;
            color: #495057;
        }}
        
        .footer {{
            margin-top: 60px;
            padding-top: 30px;
            border-top: 2px solid #e9ecef;
            text-align: center;
            color: #6c757d;
            font-size: 0.9em;
        }}
        
        ul {{
            margin: 15px 0;
            padding-left: 25px;
        }}
        
        li {{
            margin: 10px 0;
            line-height: 1.6;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{t['report']}</h1>
            <p class="date">{datetime.now().strftime("%d/%m/%Y %H:%M")}</p>
        </div>
        
        <button class="print-button no-print" onclick="window.print()">{t['print_btn']}</button>
"""
    
    # Résumé Exécutif
    html += f"""
        <h2>📋 {t['summary']}</h2>
        <div class="insight-box">
            <p>{ai_insights.get('resume_executif', 'N/A')}</p>
        </div>
"""
    
    # Vue d'ensemble
    html += f"""
        <h2>📊 {t['overview']}</h2>
        <div class="stat-grid">
            <div class="stat-card">
                <h3>{t['obs']}</h3>
                <p>{analysis['shape'][0]:,}</p>
            </div>
            <div class="stat-card">
                <h3>{t['vars']}</h3>
                <p>{analysis['shape'][1]}</p>
            </div>
            <div class="stat-card">
                <h3>{t['num']}</h3>
                <p>{len(analysis['numeric_cols'])}</p>
            </div>
            <div class="stat-card">
                <h3>{t['cat']}</h3>
                <p>{len(analysis['categorical_cols'])}</p>
            </div>
        </div>
"""
    
    # Statistiques détaillées
    if 'numeric_stats' in analysis and not analysis['numeric_stats'].empty:
        html += f"""
        <div class="page-break"></div>
        <h2>📈 {t['stats']}</h2>
        <table>
            <thead>
                <tr>
                    <th>Variable</th>
                    <th>Mean</th>
                    <th>Median</th>
                    <th>Std</th>
                    <th>Min</th>
                    <th>Max</th>
                </tr>
            </thead>
            <tbody>
"""
        for col in analysis['numeric_cols'][:15]:
            try:
                stats = analysis['numeric_stats'][col]
                html += f"""
                <tr>
                    <td><strong>{col}</strong></td>
                    <td>{float(stats['mean']):.2f}</td>
                    <td>{float(stats['50%']):.2f}</td>
                    <td>{float(stats['std']):.2f}</td>
                    <td>{float(stats['min']):.2f}</td>
                    <td>{float(stats['max']):.2f}</td>
                </tr>
"""
            except:
                pass
        html += """
            </tbody>
        </table>
"""
    
    # Visualisations intégrées
    if visualizations:
        html += f"""
        <div class="page-break"></div>
        <h2>📊 {t['visualizations']}</h2>
"""
        for viz_name, (fig, interpretation) in visualizations.items():
            try:
                img_data = fig_to_base64(fig)
                viz_title = viz_name.replace('_', ' ').title()
                html += f"""
        <div class="visualization">
            <h3>{viz_title}</h3>
            <img src="{img_data}" alt="{viz_title}">
            <div class="viz-interpretation">
                💡 {interpretation}
            </div>
        </div>
"""
            except Exception as e:
                print(f"Error embedding visualization {viz_name}: {e}")
    
    # Tendances principales
    if ai_insights.get('tendances_principales'):
        html += f"""
        <div class="page-break"></div>
        <h2>📈 {t['trends']}</h2>
        <ul>
"""
        for trend in ai_insights['tendances_principales']:
            html += f"            <li><strong>{trend}</strong></li>\n"
        html += """
        </ul>
"""
    
    # Analyses approfondies
    if ai_insights.get('insights'):
        html += f"""
        <h2>🔍 {t['analysis']}</h2>
"""
        for insight in ai_insights['insights']:
            titre = insight.get('titre', 'N/A')
            description = insight.get('description', 'N/A')
            html += f"""
        <div class="insight-box">
            <h3>{titre}</h3>
            <p>{description}</p>
        </div>
"""
    
    # Recommandations
    if ai_insights.get('recommandations'):
        html += f"""
        <div class="page-break"></div>
        <h2>💡 {t['reco']}</h2>
"""
        for i, rec in enumerate(ai_insights['recommandations'], 1):
            action = rec.get('action', 'N/A')
            justification = rec.get('justification', 'N/A')
            html += f"""
        <div class="recommendation">
            <h3>{i}. {action}</h3>
            <p>{justification}</p>
        </div>
"""
    
    # Conclusion
    html += f"""
        <h2>✅ {t['conclusion']}</h2>
        <div class="insight-box">
            <p>{ai_insights.get('conclusion', 'N/A')}</p>
        </div>
        
        <div class="footer">
            <p><strong>{t['generated']}</strong> | {t['powered']}</p>
            <p style="margin-top: 10px; font-size: 0.85em;">
                {datetime.now().strftime("%d %B %Y à %H:%M")}
            </p>
        </div>
    </div>
</body>
</html>
"""
    
    return html