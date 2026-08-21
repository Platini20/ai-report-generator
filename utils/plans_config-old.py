"""
Source UNIQUE de vérité pour les plans tarifaires.
Utilisé par auth_supabase.py, app.py, et le futur module Stripe (Phase 2).

⚠️ Remplace les définitions dupliquées et désynchronisées qui existaient
dans auth_trial.py (PLAN_CONFIGS) et subscription.py (PLANS).
Ne redéfinissez plus les plans ailleurs — importez depuis ce fichier.
"""

PLAN_CONFIGS = {
    "trial": {
        "name": "Trial",
        "reports_limit": 3,              # à vie (pas de reset mensuel)
        "max_file_size_mb": 10,
        "max_rows": 5000,
        "ai_modes": ["Anthropic API"],
        "export_formats": ["HTML"],
        "max_visualizations": 4,
        "price": 0,
        "stripe_price_id": None,
        "icon": "🎁",
    },
    "pro": {
        "name": "Pro",
        "reports_limit": 300,            # par mois
        "max_file_size_mb": 200,
        "max_rows": 300000,
        "ai_modes": ["Anthropic API"],
        "export_formats": ["HTML", "Word", "PDF"],
        "max_visualizations": -1,        # illimité
        "price": 19.99,
        "stripe_price_id": None,         # ℹ️ Le vrai Price ID vit dans st.secrets["STRIPE_PRICE_ID_PRO"]
                                          # (pas ici, pour éviter de committer des IDs dans Git)
        "icon": "🚀",
    },
    "enterprise": {
        "name": "Enterprise",
        "reports_limit": -1,
        "max_file_size_mb": -1,
        "max_rows": -1,
        "ai_modes": ["Anthropic API"],
        # PowerPoint listé mais pas encore codé (prévu après le module PDF) —
        # ne pas l'afficher comme disponible tant que word_export.py n'a pas
        # d'équivalent .pptx.
        "export_formats": ["HTML", "Word", "PDF"],
        "max_visualizations": -1,
        "price": None,                   # sur devis
        "stripe_price_id": None,
        "icon": "💎",
    },
}

DEFAULT_PLAN = "trial"


def get_plan(plan_id: str) -> dict:
    """Retourne la config d'un plan, avec repli sûr sur 'trial' si inconnu."""
    return PLAN_CONFIGS.get(plan_id, PLAN_CONFIGS[DEFAULT_PLAN])
