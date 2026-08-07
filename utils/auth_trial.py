"""
Système d'authentification avec essai gratuit et plans d'abonnement
Version complète : Trial + Starter + Pro + Enterprise
"""

import streamlit as st
import hashlib
import json
from datetime import datetime
from typing import Dict, Optional, Tuple

# ==========================================
# BASE DE DONNÉES SIMPLE (Fichier JSON)
# En production : Supabase/Firebase
# ==========================================

def load_users_db() -> Dict:
    """Charge la base de données des utilisateurs depuis les secrets"""
    try:
        return st.secrets.get("users_db", {})
    except:
        return {}

def get_user(email: str) -> Optional[Dict]:
    """Récupère un utilisateur"""
    users_db = load_users_db()
    return users_db.get(email)

def hash_password(password: str) -> str:
    """Hash un mot de passe"""
    return hashlib.sha256(password.encode()).hexdigest()


# ==========================================
# CONFIGURATION DES PLANS
# ==========================================

PLAN_CONFIGS = {
    "trial": {
        "name": "Trial",
        "reports_limit": 3,
        "max_file_size_mb": 100,
        "max_rows": 100000,
        "ai_modes": ["Anthropic API"],  # Trial = 3 rapports IA gratuits
        "export_formats": ["HTML", "Word"],
        "price": 0,
        "icon": "🎁"
    },
    "starter": {
        "name": "Starter",
        "reports_limit": 100,
        "max_file_size_mb": 200,
        "max_rows": 50000,
        "ai_modes": ["Anthropic API"],  # Uniquement Anthropic AI
        "export_formats": ["HTML", "Word"],
        "price": 29,
        "icon": "🚀"
    },
    "pro": {
        "name": "Pro",
        "reports_limit": 500,
        "max_file_size_mb": 500,
        "max_rows": 500000,
        "ai_modes": ["None", "Ollama (Local)", "Anthropic API"],
        "export_formats": ["HTML", "Word", "PDF"],
        "price": 99,
        "icon": "⭐"
    },
    "enterprise": {
        "name": "Enterprise",
        "reports_limit": -1,  # Illimité
        "max_file_size_mb": -1,
        "max_rows": -1,
        "ai_modes": ["None", "Ollama (Local)", "Anthropic API"],
        "export_formats": ["HTML", "Word", "PDF", "PowerPoint"],
        "price": 199,
        "icon": "💎"
    }
}


# ==========================================
# AUTO-INSCRIPTION (NOUVEAU)
# ==========================================

def save_new_user(email: str, password_hash: str, lang: str = 'fr') -> bool:
    """
    Sauvegarde un nouvel utilisateur dans session_state
    EN PRODUCTION: Sauvegarder dans une vraie base de données
    
    Args:
        email: Email de l'utilisateur
        password_hash: Hash du mot de passe
        lang: Langue
        
    Returns:
        bool: True si succès
    """
    if "registered_users" not in st.session_state:
        st.session_state.registered_users = {}
    
    st.session_state.registered_users[email] = {
        "password_hash": password_hash,
        "plan": "trial",  # Toujours commencer en trial
        "reports_used": 0,
        "reports_limit": PLAN_CONFIGS["trial"]["reports_limit"],
        "created_at": datetime.now().strftime("%Y-%m-%d"),
    }
    
    return True


def user_exists(email: str) -> bool:
    """Vérifie si un utilisateur existe déjà"""
    if get_user(email):
        return True
    
    if "registered_users" in st.session_state:
        if email in st.session_state.registered_users:
            return True
    
    return False


def get_user_from_all_sources(email: str) -> Optional[Dict]:
    """Récupère un utilisateur depuis toutes les sources"""
    user = get_user(email)
    if user:
        return user
    
    if "registered_users" in st.session_state:
        if email in st.session_state.registered_users:
            return st.session_state.registered_users[email]
    
    return None


# ==========================================
# AUTHENTIFICATION
# ==========================================

def check_login() -> bool:
    """
    Vérifie l'authentification avec auto-inscription
    Retourne True si authentifié, False sinon
    """
    ui_lang = st.session_state.get("ui_lang", "fr")
    
    # Traductions
    texts = {
        'fr': {
            'title': '🔒 Connexion',
            'app_name': 'AI Report Generator',
            'trial_badge_title': '🎁 Essai Gratuit',
            'trial_badge_text': '3 rapports offerts pour tester le service',
            'email_label': '📧 Email',
            'email_placeholder': 'votre@email.com',
            'password_label': '🔑 Mot de passe',
            'password_placeholder': 'Votre mot de passe',
            'login_button': 'Se connecter',
            'register_button': 'Créer un compte',
            'or_separator': 'ou',
            'register_title': '🆕 Créer un compte',
            'register_info': 'Créez votre compte pour commencer votre essai gratuit de 3 rapports',
            'confirm_password_label': '🔑 Confirmer le mot de passe',
            'confirm_password_placeholder': 'Confirmez votre mot de passe',
            'create_account_button': 'Créer mon compte',
            'back_to_login': '← Retour à la connexion',
            'error_empty_fields': 'Veuillez remplir tous les champs',
            'error_invalid_email': 'Email invalide',
            'error_password_mismatch': 'Les mots de passe ne correspondent pas',
            'error_password_short': 'Le mot de passe doit contenir au moins 6 caractères',
            'error_user_exists': 'Cet email est déjà utilisé',
            'error_login_failed': 'Email ou mot de passe incorrect',
            'success_account_created': '✅ Compte créé avec succès ! Vous pouvez maintenant vous connecter.',
            'pricing_info': 'Tarifs après l\'essai',
            'starter_plan': 'Starter : 29$/mois (100 rapports)',
            'pro_plan': 'Pro : 99$/mois (500 rapports)',
            'enterprise_plan': 'Enterprise : Sur devis (illimité)',
        },
        'en': {
            'title': '🔒 Login',
            'app_name': 'AI Report Generator',
            'trial_badge_title': '🎁 Free Trial',
            'trial_badge_text': '3 free reports to test the service',
            'email_label': '📧 Email',
            'email_placeholder': 'your@email.com',
            'password_label': '🔑 Password',
            'password_placeholder': 'Your password',
            'login_button': 'Sign in',
            'register_button': 'Create account',
            'or_separator': 'or',
            'register_title': '🆕 Create Account',
            'register_info': 'Create your account to start your free trial of 3 reports',
            'confirm_password_label': '🔑 Confirm password',
            'confirm_password_placeholder': 'Confirm your password',
            'create_account_button': 'Create my account',
            'back_to_login': '← Back to login',
            'error_empty_fields': 'Please fill all fields',
            'error_invalid_email': 'Invalid email',
            'error_password_mismatch': 'Passwords do not match',
            'error_password_short': 'Password must be at least 6 characters',
            'error_user_exists': 'This email is already in use',
            'error_login_failed': 'Invalid email or password',
            'success_account_created': '✅ Account created successfully! You can now sign in.',
            'pricing_info': 'Pricing after trial',
            'starter_plan': 'Starter: $29/month (100 reports)',
            'pro_plan': 'Pro: $99/month (500 reports)',
            'enterprise_plan': 'Enterprise: Custom pricing (unlimited)',
        }
    }
    
    t = texts.get(ui_lang, texts['fr'])
    
    def login_submitted():
        """Callback quand le formulaire de connexion est soumis"""
        email = st.session_state.get("login_email", "").strip().lower()
        password = st.session_state.get("login_password", "")
        
        if not email or not password:
            st.session_state["auth_error"] = t['error_empty_fields']
            return

        user = get_user_from_all_sources(email)
        
        if user and hash_password(password) == user.get("password_hash"):
            # Authentification réussie
            plan = user.get("plan", "trial")
            plan_config = PLAN_CONFIGS.get(plan, PLAN_CONFIGS["trial"])
            
            st.session_state["authenticated"] = True
            st.session_state["user_email"] = email
            st.session_state["user_plan"] = plan
            st.session_state["reports_used"] = user.get("reports_used", 0)
            st.session_state["reports_limit"] = plan_config["reports_limit"]
            st.session_state["auth_error"] = None
            st.session_state["show_register"] = False
        else:
            st.session_state["authenticated"] = False
            st.session_state["auth_error"] = t['error_login_failed']
    
    def register_submitted():
        """Callback quand le formulaire d'inscription est soumis"""
        email = st.session_state.get("register_email", "").strip().lower()
        password = st.session_state.get("register_password", "")
        confirm = st.session_state.get("register_confirm", "")
        
        if not email or not password or not confirm:
            st.session_state["register_error"] = t['error_empty_fields']
            return
        
        if "@" not in email or "." not in email:
            st.session_state["register_error"] = t['error_invalid_email']
            return
        
        if password != confirm:
            st.session_state["register_error"] = t['error_password_mismatch']
            return
        
        if len(password) < 6:
            st.session_state["register_error"] = t['error_password_short']
            return
        
        if user_exists(email):
            st.session_state["register_error"] = t['error_user_exists']
            return
        
        # Créer le compte
        password_hash = hash_password(password)
        if save_new_user(email, password_hash, ui_lang):
            st.session_state["register_success"] = True
            st.session_state["register_error"] = None
            st.session_state["show_register"] = False
    
    # Vérifier si déjà authentifié
    if st.session_state.get("authenticated"):
        return True
    
    # Afficher le formulaire de connexion/inscription
    st.markdown("""
        <style>
            .login-container {
                max-width: 500px;
                margin: 0 auto;
                padding: 2rem;
            }
            .login-header {
                text-align: center;
                margin-bottom: 2rem;
            }
            .login-title {
                font-size: 2.5rem;
                font-weight: 800;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                margin-bottom: 0.5rem;
            }
            .trial-badge {
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                color: white;
                padding: 0.8rem 1.5rem;
                border-radius: 12px;
                margin: 1.5rem 0;
                text-align: center;
                box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
            }
            .pricing-box {
                background: #f8f9fa;
                padding: 1rem;
                border-radius: 8px;
                margin: 1rem 0;
                font-size: 0.9rem;
            }
        </style>
    """, unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        
        # Header
        st.markdown(f"""
            <div class="login-header">
                <h1 class="login-title">{t['app_name']}</h1>
                <p style="font-size: 1.1rem; color: #6b7280;">{t['title']}</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Badge essai gratuit
        st.markdown(f"""
            <div class="trial-badge">
                <div style="font-size: 1.5rem; font-weight: 700; margin-bottom: 0.3rem;">
                    {t['trial_badge_title']}
                </div>
                <div style="font-size: 0.95rem; opacity: 0.95;">
                    {t['trial_badge_text']}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Afficher le formulaire d'inscription ou de connexion
        show_register = st.session_state.get("show_register", False)
        
        if show_register:
            # FORMULAIRE D'INSCRIPTION
            st.markdown(f"### {t['register_title']}")
            st.info(t['register_info'])
            
            # Message de succès si inscription réussie
            if st.session_state.get("register_success"):
                st.success(t['success_account_created'])
                if st.button(t['back_to_login'], use_container_width=True):
                    st.session_state["show_register"] = False
                    st.session_state["register_success"] = False
                    st.rerun()
            else:
                # Afficher les erreurs
                if st.session_state.get("register_error"):
                    st.error(st.session_state["register_error"])
                
                # Champs du formulaire
                st.text_input(
                    t['email_label'],
                    key="register_email",
                    placeholder=t['email_placeholder']
                )
                
                st.text_input(
                    t['password_label'],
                    type="password",
                    key="register_password",
                    placeholder=t['password_placeholder']
                )
                
                st.text_input(
                    t['confirm_password_label'],
                    type="password",
                    key="register_confirm",
                    placeholder=t['confirm_password_placeholder']
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button(t['create_account_button'], type="primary", use_container_width=True):
                        register_submitted()
                        st.rerun()
                
                with col2:
                    if st.button(t['back_to_login'], use_container_width=True):
                        st.session_state["show_register"] = False
                        st.session_state["register_error"] = None
                        st.rerun()
        
        else:
            # FORMULAIRE DE CONNEXION
            # Afficher les erreurs
            if st.session_state.get("auth_error"):
                st.error(st.session_state["auth_error"])
            
            # Champs du formulaire
            st.text_input(
                t['email_label'],
                key="login_email",
                placeholder=t['email_placeholder']
            )
            
            st.text_input(
                t['password_label'],
                type="password",
                key="login_password",
                placeholder=t['password_placeholder']
            )
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button(t['login_button'], type="primary", use_container_width=True):
                    login_submitted()
                    st.rerun()
            
            with col2:
                if st.button(t['register_button'], use_container_width=True):
                    st.session_state["show_register"] = True
                    st.session_state["auth_error"] = None
                    st.rerun()
        
        # Tarifs
        st.markdown("---")
        st.markdown(f"""
            <div class="pricing-box">
                <strong>{t['pricing_info']}</strong><br/>
                🚀 {t['starter_plan']}<br/>
                ⭐ {t['pro_plan']}<br/>
                💎 {t['enterprise_plan']}
            </div>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    return False


# ==========================================
# GESTION DES QUOTAS
# ==========================================

def can_generate_report() -> Tuple[bool, str]:
    """
    Vérifie si l'utilisateur peut générer un rapport
    
    Returns:
        tuple: (can_generate, message)
    """
    if not st.session_state.get("authenticated"):
        return False, "Non authentifié"
    
    plan = st.session_state.get("user_plan", "trial")
    reports_used = st.session_state.get("reports_used", 0)
    reports_limit = st.session_state.get("reports_limit", 3)
    
    # Si limite illimitée (enterprise)
    if reports_limit == -1:
        return True, ""
    
    # Vérifier la limite
    if reports_used >= reports_limit:
        if plan == "trial":
            return False, "Essai gratuit épuisé"
        else:
            return False, f"Limite mensuelle atteinte ({reports_limit} rapports)"
    
    return True, ""


def increment_report_count():
    """Incrémente le compteur de rapports utilisés"""
    if "reports_used" in st.session_state:
        st.session_state.reports_used += 1
        
        # Si l'utilisateur est dans registered_users, mettre à jour
        email = st.session_state.get("user_email")
        if email and "registered_users" in st.session_state:
            if email in st.session_state.registered_users:
                st.session_state.registered_users[email]["reports_used"] = st.session_state.reports_used


def get_quota_info() -> Dict:
    """Retourne les informations de quota de l'utilisateur"""
    plan = st.session_state.get("user_plan", "trial")
    used = st.session_state.get("reports_used", 0)
    limit = st.session_state.get("reports_limit", 3)
    
    if limit == -1:
        remaining = -1  # Illimité
        percentage = 0
    else:
        remaining = max(0, limit - used)
        percentage = (used / limit * 100) if limit > 0 else 0
    
    return {
        "plan": plan,
        "used": used,
        "limit": limit,
        "remaining": remaining,
        "percentage": percentage,
        "is_trial": plan == "trial",
        "is_expired": used >= limit if limit != -1 else False
    }


# ==========================================
# UI HELPER
# ==========================================

def show_quota_sidebar():
    """Affiche le quota dans la sidebar"""
    if not st.session_state.get("authenticated"):
        return
    
    ui_lang = st.session_state.get("ui_lang", "fr")
    quota = get_quota_info()
    plan_config = PLAN_CONFIGS.get(quota["plan"], PLAN_CONFIGS["trial"])
    
    st.markdown("---")
    
    # Traductions
    if ui_lang == 'fr':
        used_label = "Utilisés"
        remaining_label = "Restants"
        trial_ended = "⚠️ Essai gratuit terminé"
        continue_text = "Continuez à utiliser le service :"
        contact_text = "📧 Contact : agouanetf@yahoo.com"
        pricing_title = "Tarifs :"
        warning_remaining_trial = f"⚠️ Plus que {quota['remaining']} rapport(s) gratuit(s) !"
        warning_remaining_paid = f"⚠️ Plus que {quota['remaining']} rapport(s) ce mois"
        think_subscribe = "💡 Pensez à vous abonner pour continuer"
        unlimited = "Illimité ♾️"
    else:
        used_label = "Used"
        remaining_label = "Remaining"
        trial_ended = "⚠️ Free trial ended"
        continue_text = "Continue using the service:"
        contact_text = "📧 Contact: agouanetf@yahoo.com"
        pricing_title = "Pricing:"
        warning_remaining_trial = f"⚠️ Only {quota['remaining']} free report(s) left!"
        warning_remaining_paid = f"⚠️ Only {quota['remaining']} report(s) left this month"
        think_subscribe = "💡 Consider subscribing to continue"
        unlimited = "Unlimited ♾️"
    
    # Badge du plan
    plan_display = f"{plan_config['icon']} {plan_config['name']}"
    
    if quota["is_trial"]:
        if quota["is_expired"]:
            st.error(f"🚫 {plan_display}")
        else:
            st.info(f"🎁 {plan_display}")
    else:
        if quota["plan"] == "enterprise":
            st.success(f"💎 {plan_display}")
        elif quota["plan"] == "pro":
            st.success(f"⭐ {plan_display}")
        else:
            st.success(f"🚀 {plan_display}")
    
    # Progress bar
    if quota["limit"] > 0:
        st.progress(min(quota["percentage"] / 100, 1.0))
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(used_label, quota["used"])
    with col2:
        if quota["limit"] == -1:
            st.metric(remaining_label, unlimited)
        else:
            st.metric(remaining_label, quota["remaining"])
    
    # Avertissements
    if quota["is_trial"] and quota["is_expired"]:
        st.error(f"**{trial_ended}**")
        st.markdown(f"""
        **{continue_text}**
        
        {contact_text}
        
        **{pricing_title}**
        - 🚀 Starter: $29/mois (100 rapports)
        - ⭐ Pro: $99/mois (500 rapports)
        - 💎 Enterprise: Sur devis (illimité)
        """)
    
    elif quota["is_trial"] and quota["remaining"] <= 1:
        st.warning(warning_remaining_trial)
        st.info(think_subscribe)
    
    elif not quota["is_trial"] and quota["limit"] != -1 and quota["remaining"] <= 5:
        st.warning(warning_remaining_paid)


def show_upgrade_message():
    """Affiche le message pour passer à un plan payant"""
    ui_lang = st.session_state.get("ui_lang", "fr")
    quota = get_quota_info()
    
    st.error("🚫 **" + ("Limite atteinte" if ui_lang == 'fr' else "Limit reached") + "**")
    
    if quota["is_trial"]:
        if ui_lang == 'fr':
            st.markdown("""
            ### 🎉 Vous avez utilisé vos 3 rapports gratuits !
            
            **Le service vous plaît ?** Passez à un plan payant pour continuer :
            
            #### 📋 Nos Offres
            
            **🚀 Starter - 29$/mois**
            - ✅ 100 rapports/mois
            - ✅ 50 MB max par fichier
            - ✅ 50,000 lignes max
            - ✅ Ollama local
            - ✅ Export HTML + Word
            
            **⭐ Pro - 99$/mois** ⭐ Populaire
            - ✅ 500 rapports/mois
            - ✅ 200 MB max par fichier
            - ✅ 500,000 lignes max
            - ✅ Tous modes IA (Ollama + Anthropic)
            - ✅ Export HTML + Word + PDF
            - ✅ Templates personnalisés
            - ✅ Rapports planifiés
            - ✅ Accès API
            
            **💎 Enterprise - Sur devis**
            - ✅ Rapports illimités
            - ✅ Fichiers illimités
            - ✅ Lignes illimitées
            - ✅ Tous modes IA
            - ✅ Tous formats export
            - ✅ Support dédié 24/7
            
            ---
            
            📧 **Contact** : agouanetf@yahoo.com  
            💬 **Sujet** : Abonnement AI Report Generator
            """)
        else:
            st.markdown("""
            ### 🎉 You've used your 3 free reports!
            
            **Enjoyed the service?** Upgrade to a paid plan to continue:
            
            #### 📋 Our Plans
            
            **🚀 Starter - $29/month**
            - ✅ 100 reports/month
            - ✅ 50 MB max per file
            - ✅ 50,000 rows max
            - ✅ Ollama local
            - ✅ HTML + Word export
            
            **⭐ Pro - $99/month** ⭐ Popular
            - ✅ 500 reports/month
            - ✅ 200 MB max per file
            - ✅ 500,000 rows max
            - ✅ All AI modes (Ollama + Anthropic)
            - ✅ HTML + Word + PDF export
            - ✅ Custom templates
            - ✅ Scheduled reports
            - ✅ API access
            
            **💎 Enterprise - Custom pricing**
            - ✅ Unlimited reports
            - ✅ Unlimited file size
            - ✅ Unlimited rows
            - ✅ All AI modes
            - ✅ All export formats
            - ✅ Dedicated support 24/7
            
            ---
            
            📧 **Contact**: agouanetf@yahoo.com  
            💬 **Subject**: AI Report Generator Subscription
            """)
    else:
        if ui_lang == 'fr':
            st.markdown(f"""
            ### ⚠️ Limite mensuelle atteinte
            
            Vous avez utilisé vos **{quota['limit']} rapports** de ce mois.
            
            **Options :**
            - ⏳ Attendez le mois prochain
            - 📈 Passez au plan supérieur
            
            📧 **Contact** : agouanetf@yahoo.com
            """)
        else:
            st.markdown(f"""
            ### ⚠️ Monthly limit reached
            
            You've used your **{quota['limit']} reports** for this month.
            
            **Options:**
            - ⏳ Wait for next month
            - 📈 Upgrade to higher plan
            
            📧 **Contact**: agouanetf@yahoo.com
            """)


def logout():
    """Déconnexion"""
    keys_to_delete = [
        "authenticated", "user_email", "user_plan", 
        "reports_used", "reports_limit", "auth_error",
        "register_error", "register_success", "show_register"
    ]
    for key in keys_to_delete:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()
