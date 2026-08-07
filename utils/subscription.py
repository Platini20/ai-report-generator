"""
Gestion des plans d'abonnement et limites
Version simulation (sans DB)
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class SubscriptionPlan:
    """Définition d'un plan d'abonnement"""
    name: str
    display_name: str
    price_monthly: float
    price_yearly: Optional[float]
    
    # Limites
    reports_per_month: int  # -1 = illimité
    max_file_size_mb: int
    max_rows: int
    max_visualizations: int
    
    # Fonctionnalités
    ai_modes: List[str]
    export_formats: List[str]
    templates_enabled: bool
    scheduled_reports_enabled: bool
    api_access: bool
    support_level: str
    
    # Messaging
    badge_color: str
    badge_icon: str
    description: str


# Définition des plans
PLANS = {
    'starter': SubscriptionPlan(
        name='starter',
        display_name='Starter',
        price_monthly=29,
        price_yearly=290,  # ~2 mois offerts
        reports_per_month=100,
        max_file_size_mb=100,
        max_rows=50000,
        max_visualizations=6,
        ai_modes=['Anthropic API'],  # Uniquement Anthropic AI
        export_formats=['HTML', 'Word'],
        templates_enabled=False,
        scheduled_reports_enabled=False,
        api_access=False,
        support_level='Email (24h)',
        badge_color='#10b981',
        badge_icon='🚀',
        description='Parfait pour débuter avec l\'IA'
    ),
    
    'pro': SubscriptionPlan(
        name='pro',
        display_name='Pro',
        price_monthly=99,
        price_yearly=990,  # ~2 mois offerts
        reports_per_month=500,
        max_file_size_mb=500,
        max_rows=500000,
        max_visualizations=12,
        ai_modes=['Anthropic API'],  # Uniquement Anthropic AI
        export_formats=['HTML', 'Word', 'PDF'],
        templates_enabled=True,
        scheduled_reports_enabled=True,
        api_access=True,
        support_level='Email + Chat (12h)',
        badge_color='#667eea',
        badge_icon='⭐',
        description='Pour les professionnels exigeants'
    ),
    
    'enterprise': SubscriptionPlan(
        name='enterprise',
        display_name='Enterprise',
        price_monthly=299,
        price_yearly=2990,
        reports_per_month=-1,  # Illimité
        max_file_size_mb=-1,
        max_rows=-1,
        max_visualizations=-1,
        ai_modes=['Anthropic API'],  # Uniquement Anthropic AI
        export_formats=['HTML', 'Word', 'PDF', 'PowerPoint'],
        templates_enabled=True,
        scheduled_reports_enabled=True,
        api_access=True,
        support_level='Prioritaire 24/7 + Account Manager',
        badge_color='#f59e0b',
        badge_icon='💎',
        description='Solution complète pour les entreprises'
    ),
    }


def get_plan(plan_name: str) -> SubscriptionPlan:
    """Récupère un plan par son nom"""
    return PLANS.get(plan_name.lower(), PLANS['starter'])


def check_limit(plan: SubscriptionPlan, limit_type: str, current_value: int, lang: str = 'fr') -> tuple[bool, str]:
    """
    Vérifie si une limite est atteinte
    
    Args:
        plan: Plan d'abonnement
        limit_type: Type de limite ('reports', 'file_size', 'rows', 'visualizations')
        current_value: Valeur actuelle
        lang: Langue ('fr' ou 'en')
        
    Returns:
        tuple: (is_allowed, message)
    """
    
    messages = {
        'fr': {
            'reports_limit': "⚠️ Limite atteinte : {} rapports maximum avec le plan {}",
            'reports_warning': "⚠️ Attention : {} rapport(s) restant(s) ce mois-ci",
            'file_size_limit': "⚠️ Fichier trop volumineux : {} MB (limite: {} MB en plan {})",
            'rows_limit': "⚠️ Trop de lignes : {:,} lignes (limite: {:,} en plan {})",
            'viz_limit': "⚠️ Trop de visualisations : {} (limite: {} en plan {})",
        },
        'en': {
            'reports_limit': "⚠️ Limit reached: {} reports maximum with {} plan",
            'reports_warning': "⚠️ Warning: {} report(s) remaining this month",
            'file_size_limit': "⚠️ File too large: {} MB (limit: {} MB in {} plan)",
            'rows_limit': "⚠️ Too many rows: {:,} rows (limit: {:,} in {} plan)",
            'viz_limit': "⚠️ Too many visualizations: {} (limit: {} in {} plan)",
        }
    }
    
    msg = messages.get(lang, messages['fr'])
    
    if limit_type == 'reports':
        limit = plan.reports_per_month
        if limit == -1:
            return True, ""
        
        if current_value >= limit:
            return False, msg['reports_limit'].format(limit, plan.display_name)
        
        remaining = limit - current_value
        if remaining <= 5:
            return True, msg['reports_warning'].format(remaining)
        
        return True, ""
    
    elif limit_type == 'file_size':
        limit = plan.max_file_size_mb
        if limit == -1:
            return True, ""
        
        if current_value > limit:
            return False, msg['file_size_limit'].format(int(current_value), limit, plan.display_name)
        
        return True, ""
    
    elif limit_type == 'rows':
        limit = plan.max_rows
        if limit == -1:
            return True, ""
        
        if current_value > limit:
            return False, msg['rows_limit'].format(current_value, limit, plan.display_name)
        
        return True, ""
    
    elif limit_type == 'visualizations':
        limit = plan.max_visualizations
        if limit == -1:
            return True, ""
        
        if current_value > limit:
            return False, msg['viz_limit'].format(current_value, limit, plan.display_name)
        
        return True, ""
    
    return True, ""


def get_upgrade_message(current_plan: SubscriptionPlan, feature: str, lang: str = 'fr') -> str:
    """Génère un message d'upgrade pour une fonctionnalité bloquée"""
    
    messages = {
        'fr': {
            'ai_anthropic': "🔒 Anthropic API disponible en plan PRO. Passez au plan PRO pour débloquer Claude AI.",
            'export_pdf': "🔒 Export PDF disponible en plan PRO.",
            'export_ppt': "🔒 Export PowerPoint disponible en plan ENTERPRISE uniquement.",
            'templates': "🔒 Templates personnalisés disponibles en plan PRO.",
            'scheduled': "🔒 Rapports planifiés disponibles en plan PRO.",
            'api': "🔒 Accès API disponible en plan PRO.",
            'more_reports': "💡 Besoin de plus de rapports ? Passez au plan {} pour générer {} rapports/mois !",
            'unlimited': "💡 Besoin de rapports illimités ? Passez au plan ENTERPRISE !",
            'file_size': "📁 Fichier trop volumineux ? Le plan {} supporte jusqu'à {} MB.",
            'rows': "📊 Dataset trop grand ? Le plan {} supporte jusqu'à {:,} lignes.",
        },
        'en': {
            'ai_anthropic': "🔒 Anthropic API available in PRO plan. Upgrade to unlock Claude AI.",
            'export_pdf': "🔒 PDF export available in PRO plan.",
            'export_ppt': "🔒 PowerPoint export available in ENTERPRISE plan only.",
            'templates': "🔒 Custom templates available in PRO plan.",
            'scheduled': "🔒 Scheduled reports available in PRO plan.",
            'api': "🔒 API access available in PRO plan.",
            'more_reports': "💡 Need more reports? Upgrade to {} plan for {} reports/month!",
            'unlimited': "💡 Need unlimited reports? Upgrade to ENTERPRISE plan!",
            'file_size': "📁 File too large? {} plan supports up to {} MB.",
            'rows': "📊 Dataset too big? {} plan supports up to {:,} rows.",
        }
    }
    
    msg = messages.get(lang, messages['fr'])
    return msg.get(feature, "")


def get_next_plan_suggestion(current_plan_name: str, reason: str = 'reports', lang: str = 'fr') -> tuple[str, str]:
    """
    Suggère le prochain plan à prendre selon le plan actuel et la raison
    
    Args:
        current_plan_name: Nom du plan actuel
        reason: Raison de l'upgrade ('reports', 'ai', 'export', etc.)
        lang: Langue
        
    Returns:
        tuple: (next_plan_name, upgrade_message)
    """
    
    if current_plan_name == 'starter':
        next_plan = PLANS['pro']
        
        if reason == 'reports':
            msg = get_upgrade_message(PLANS['starter'], 'more_reports', lang)
            msg = msg.format(next_plan.display_name, next_plan.reports_per_month)
        elif reason == 'ai':
            msg = get_upgrade_message(PLANS['starter'], 'ai_anthropic', lang)
        elif reason == 'export_pdf':
            msg = get_upgrade_message(PLANS['starter'], 'export_pdf', lang)
        elif reason == 'templates':
            msg = get_upgrade_message(PLANS['starter'], 'templates', lang)
        elif reason == 'api':
            msg = get_upgrade_message(PLANS['starter'], 'api', lang)
        else:
            msg = f"⭐ Passez au plan PRO pour plus de fonctionnalités !" if lang == 'fr' else "⭐ Upgrade to PRO for more features!"
        
        return 'pro', msg
    
    elif current_plan_name == 'pro':
        next_plan = PLANS['enterprise']
        
        if reason == 'reports':
            msg = get_upgrade_message(PLANS['pro'], 'unlimited', lang)
        elif reason == 'export_ppt':
            msg = get_upgrade_message(PLANS['pro'], 'export_ppt', lang)
        else:
            msg = f"💎 Passez au plan ENTERPRISE pour un accès illimité !" if lang == 'fr' else "💎 Upgrade to ENTERPRISE for unlimited access!"
        
        return 'enterprise', msg
    
    else:  # enterprise
        return 'enterprise', ""


def format_plan_badge(plan: SubscriptionPlan, lang: str = 'fr') -> str:
    """Génère un badge HTML pour afficher le plan actuel"""
    
    if plan.name == 'enterprise':
        price_text = "Sur devis" if lang == 'fr' else "Custom pricing"
    else:
        price_text = f"${plan.price_monthly}/mois" if lang == 'fr' else f"${plan.price_monthly}/mo"
    
    return f"""
    <div style="background: {plan.badge_color}; color: white; 
                padding: 0.8rem 1.2rem; border-radius: 12px; 
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                margin: 1rem 0;">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <div style="font-size: 0.75rem; opacity: 0.9; text-transform: uppercase; letter-spacing: 1px;">
                    {'Plan Actuel' if lang == 'fr' else 'Current Plan'}
                </div>
                <div style="font-size: 1.5rem; font-weight: 800; margin: 0.2rem 0;">
                    {plan.badge_icon} {plan.display_name.upper()}
                </div>
                <div style="font-size: 0.85rem; opacity: 0.95;">
                    {price_text}
                </div>
            </div>
        </div>
    </div>
    """


def get_plan_features_summary(plan: SubscriptionPlan, lang: str = 'fr') -> str:
    """Génère un résumé des fonctionnalités du plan en HTML"""
    
    if plan.reports_per_month == -1:
        reports_text = "Illimité ♾️" if lang == 'fr' else "Unlimited ♾️"
    else:
        reports_text = f"{plan.reports_per_month} {'rapports/mois' if lang == 'fr' else 'reports/month'}"
    
    if plan.max_file_size_mb == -1:
        file_size_text = "Illimité ♾️" if lang == 'fr' else "Unlimited ♾️"
    else:
        file_size_text = f"{plan.max_file_size_mb} MB"
    
    if plan.max_rows == -1:
        rows_text = "Illimité ♾️" if lang == 'fr' else "Unlimited ♾️"
    else:
        rows_text = f"{plan.max_rows:,} {'lignes' if lang == 'fr' else 'rows'}"
    
    ai_text = ", ".join(plan.ai_modes[:2])
    if len(plan.ai_modes) > 2:
        ai_text += f" + {len(plan.ai_modes) - 2}"
    
    exports_text = ", ".join(plan.export_formats)
    
    return f"""
    <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin: 1rem 0;">
        <div style="font-size: 0.85rem; color: #495057;">
            <div style="margin: 0.5rem 0;"><strong>📊 {'Rapports' if lang == 'fr' else 'Reports'}:</strong> {reports_text}</div>
            <div style="margin: 0.5rem 0;"><strong>📁 {'Fichier max' if lang == 'fr' else 'Max file'}:</strong> {file_size_text}</div>
            <div style="margin: 0.5rem 0;"><strong>📈 {'Lignes max' if lang == 'fr' else 'Max rows'}:</strong> {rows_text}</div>
            <div style="margin: 0.5rem 0;"><strong>🧠 {'Modes IA' if lang == 'fr' else 'AI Modes'}:</strong> {ai_text}</div>
            <div style="margin: 0.5rem 0;"><strong>💾 {'Exports' if lang == 'fr' else 'Exports'}:</strong> {exports_text}</div>
            <div style="margin: 0.5rem 0;"><strong>💬 {'Support' if lang == 'fr' else 'Support'}:</strong> {plan.support_level}</div>
        </div>
    </div>
    """


def get_pricing_comparison(lang: str = 'fr') -> str:
    """Génère un tableau de comparaison des plans"""
    
    if lang == 'fr':
        html = """
        <style>
            .pricing-table {
                width: 100%;
                border-collapse: collapse;
                margin: 2rem 0;
                font-size: 0.85rem;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .pricing-table th {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 1rem 0.5rem;
                text-align: center;
                font-weight: 700;
                font-size: 0.9rem;
            }
            .pricing-table td {
                padding: 0.8rem 0.5rem;
                text-align: center;
                border-bottom: 1px solid #e5e7eb;
            }
            .pricing-table tr:hover {
                background-color: #f8f9fa;
            }
            .pricing-table .feature-name {
                text-align: left;
                font-weight: 600;
                color: #374151;
            }
            .check { color: #10b981; font-size: 1.1rem; font-weight: bold; }
            .cross { color: #ef4444; font-size: 1.1rem; font-weight: bold; }
            .plan-header {
                font-size: 1.1rem !important;
                padding: 1.2rem 0.5rem !important;
            }
            .price {
                font-size: 0.85rem;
                opacity: 0.95;
                font-weight: 500;
            }
        </style>
        
        <table class="pricing-table">
            <thead>
                <tr>
                    <th style="text-align: left;">Fonctionnalité</th>
                    <th class="plan-header">🚀 STARTER<br/><span class="price">29$/mois</span></th>
                    <th class="plan-header">⭐ PRO<br/><span class="price">99$/mois</span></th>
                    <th class="plan-header">💎 ENTERPRISE<br/><span class="price">299$/mois</span></th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td class="feature-name">📊 Rapports / mois</td>
                    <td><strong>100</strong></td>
                    <td><strong>500</strong></td>
                    <td><strong>Illimité ♾️</strong></td>
                </tr>
                <tr>
                    <td class="feature-name">📁 Taille fichier max</td>
                    <td>50 MB</td>
                    <td>200 MB</td>
                    <td>Illimité ♾️</td>
                </tr>
                <tr>
                    <td class="feature-name">📈 Lignes max</td>
                    <td>50,000</td>
                    <td>500,000</td>
                    <td>Illimité ♾️</td>
                </tr>
                <tr>
                    <td class="feature-name">🧠 Modes IA</td>
                    <td>Basique + Ollama</td>
                    <td><strong>Tous modes</strong></td>
                    <td><strong>Tous + Custom</strong></td>
                </tr>
                <tr>
                    <td class="feature-name">💾 Formats export</td>
                    <td>HTML, Word</td>
                    <td>HTML, Word, PDF</td>
                    <td>Tous formats</td>
                </tr>
                <tr>
                    <td class="feature-name">📊 Visualisations</td>
                    <td>6</td>
                    <td>12</td>
                    <td>Illimité ♾️</td>
                </tr>
                <tr>
                    <td class="feature-name">📝 Templates personnalisés</td>
                    <td><span class="cross">✗</span></td>
                    <td><span class="check">✓</span></td>
                    <td><span class="check">✓</span></td>
                </tr>
                <tr>
                    <td class="feature-name">⏰ Rapports planifiés</td>
                    <td><span class="cross">✗</span></td>
                    <td><span class="check">✓</span></td>
                    <td><span class="check">✓</span></td>
                </tr>
                <tr>
                    <td class="feature-name">🔌 Accès API</td>
                    <td><span class="cross">✗</span></td>
                    <td><span class="check">✓</span></td>
                    <td><span class="check">✓</span></td>
                </tr>
                <tr>
                    <td class="feature-name">💬 Support</td>
                    <td>Email (24h)</td>
                    <td>Email + Chat (12h)</td>
                    <td>Prioritaire 24/7</td>
                </tr>
                <tr>
                    <td class="feature-name">💰 Prix annuel</td>
                    <td><strong>290$/an</strong><br/><small>(~2 mois offerts)</small></td>
                    <td><strong>990$/an</strong><br/><small>(~2 mois offerts)</small></td>
                    <td><strong>2,990$/an</strong><br/><small>(~2 mois offerts)</small></td>
                </tr>
            </tbody>
        </table>
        """
    else:
        html = """
        <style>
            .pricing-table {
                width: 100%;
                border-collapse: collapse;
                margin: 2rem 0;
                font-size: 0.85rem;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .pricing-table th {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 1rem 0.5rem;
                text-align: center;
                font-weight: 700;
                font-size: 0.9rem;
            }
            .pricing-table td {
                padding: 0.8rem 0.5rem;
                text-align: center;
                border-bottom: 1px solid #e5e7eb;
            }
            .pricing-table tr:hover {
                background-color: #f8f9fa;
            }
            .pricing-table .feature-name {
                text-align: left;
                font-weight: 600;
                color: #374151;
            }
            .check { color: #10b981; font-size: 1.1rem; font-weight: bold; }
            .cross { color: #ef4444; font-size: 1.1rem; font-weight: bold; }
            .plan-header {
                font-size: 1.1rem !important;
                padding: 1.2rem 0.5rem !important;
            }
            .price {
                font-size: 0.85rem;
                opacity: 0.95;
                font-weight: 500;
            }
        </style>
        
        <table class="pricing-table">
            <thead>
                <tr>
                    <th style="text-align: left;">Feature</th>
                    <th class="plan-header">🚀 STARTER<br/><span class="price">$29/month</span></th>
                    <th class="plan-header">⭐ PRO<br/><span class="price">$99/month</span></th>
                    <th class="plan-header">💎 ENTERPRISE<br/><span class="price">$299/month</span></th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td class="feature-name">📊 Reports / month</td>
                    <td><strong>100</strong></td>
                    <td><strong>500</strong></td>
                    <td><strong>Unlimited ♾️</strong></td>
                </tr>
                <tr>
                    <td class="feature-name">📁 Max file size</td>
                    <td>50 MB</td>
                    <td>200 MB</td>
                    <td>Unlimited ♾️</td>
                </tr>
                <tr>
                    <td class="feature-name">📈 Max rows</td>
                    <td>50,000</td>
                    <td>500,000</td>
                    <td>Unlimited ♾️</td>
                </tr>
                <tr>
                    <td class="feature-name">🧠 AI Modes</td>
                    <td>Basic + Ollama</td>
                    <td><strong>All modes</strong></td>
                    <td><strong>All + Custom</strong></td>
                </tr>
                <tr>
                    <td class="feature-name">💾 Export formats</td>
                    <td>HTML, Word</td>
                    <td>HTML, Word, PDF</td>
                    <td>All formats</td>
                </tr>
                <tr>
                    <td class="feature-name">📊 Visualizations</td>
                    <td>6</td>
                    <td>12</td>
                    <td>Unlimited ♾️</td>
                </tr>
                <tr>
                    <td class="feature-name">📝 Custom templates</td>
                    <td><span class="cross">✗</span></td>
                    <td><span class="check">✓</span></td>
                    <td><span class="check">✓</span></td>
                </tr>
                <tr>
                    <td class="feature-name">⏰ Scheduled reports</td>
                    <td><span class="cross">✗</span></td>
                    <td><span class="check">✓</span></td>
                    <td><span class="check">✓</span></td>
                </tr>
                <tr>
                    <td class="feature-name">🔌 API Access</td>
                    <td><span class="cross">✗</span></td>
                    <td><span class="check">✓</span></td>
                    <td><span class="check">✓</span></td>
                </tr>
                <tr>
                    <td class="feature-name">💬 Support</td>
                    <td>Email (24h)</td>
                    <td>Email + Chat (12h)</td>
                    <td>Priority 24/7</td>
                </tr>
                <tr>
                    <td class="feature-name">💰 Annual price</td>
                    <td><strong>$290/year</strong><br/><small>(~2 months free)</small></td>
                    <td><strong>$990/year</strong><br/><small>(~2 months free)</small></td>
                    <td><strong>$2,990/year</strong><br/><small>(~2 months free)</small></td>
                </tr>
            </tbody>
        </table>
        """
    
    return html


def get_upgrade_button_html(target_plan: str, lang: str = 'fr') -> str:
    """Génère un bouton d'upgrade stylisé"""
    
    plan = PLANS[target_plan]
    
    if lang == 'fr':
        text = f"⭐ Passer au plan {plan.display_name.upper()}"
        subtext = f"${plan.price_monthly}/mois • {plan.reports_per_month if plan.reports_per_month != -1 else '∞'} rapports"
    else:
        text = f"⭐ Upgrade to {plan.display_name.upper()}"
        subtext = f"${plan.price_monthly}/month • {plan.reports_per_month if plan.reports_per_month != -1 else '∞'} reports"
    
    return f"""
    <div style="background: linear-gradient(135deg, {plan.badge_color} 0%, {plan.badge_color}dd 100%);
                padding: 1.2rem;
                border-radius: 12px;
                text-align: center;
                margin: 1rem 0;
                box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                cursor: pointer;
                transition: transform 0.2s;">
        <div style="color: white; font-size: 1.2rem; font-weight: 700; margin-bottom: 0.3rem;">
            {text}
        </div>
        <div style="color: white; opacity: 0.95; font-size: 0.9rem;">
            {subtext}
        </div>
    </div>
    """
