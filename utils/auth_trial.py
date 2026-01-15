"""
Système d'authentification avec essai gratuit et auto-inscription
Version complète avec traductions FR/EN
"""

import streamlit as st
import hashlib
import json
from datetime import datetime
from typing import Dict, Optional, Tuple

# ==========================================
# BASE DE DONNÉES SIMPLE (Fichier JSON)
# En production : utiliser Supabase/Firebase
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
    # Pour MVP: stocker dans session_state
    # En production: appeler API Supabase/Firebase
    
    if "registered_users" not in st.session_state:
        st.session_state.registered_users = {}
    
    st.session_state.registered_users[email] = {
        "password_hash": password_hash,
        "plan": "trial",
        "reports_used": 0,
        "reports_limit": 3,
        "created_at": datetime.now().strftime("%Y-%m-%d"),
    }
    
    return True


def user_exists(email: str) -> bool:
    """Vérifie si un utilisateur existe déjà"""
    # Vérifier dans secrets
    if get_user(email):
        return True
    
    # Vérifier dans les nouveaux inscrits (session)
    if "registered_users" in st.session_state:
        if email in st.session_state.registered_users:
            return True
    
    return False


def get_user_from_all_sources(email: str) -> Optional[Dict]:
    """Récupère un utilisateur depuis toutes les sources"""
    # D'abord les secrets (utilisateurs pré-configurés)
    user = get_user(email)
    if user:
        return user
    
    # Ensuite les nouveaux inscrits (session)
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
    
    # Récupérer la langue de l'interface (par défaut FR)
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
        
        # Récupérer l'utilisateur depuis toutes les sources
        user = get_user_from_all_sources(email)
        
        if user and hash_password(password) == user.get("password_hash"):
            # Authentification réussie
            st.session_state["authenticated"] = True
            st.session_state["user_email"] = email
            st.session_state["user_plan"] = user.get("plan", "trial")
            st.session_state["reports_used"] = user.get("reports_used", 0)
            st.session_state["reports_limit"] = user.get("reports_limit", 3)
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
        
        # Validation
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
            st.session_state["register_success"] = t['success_account_created']
            st.session_state["register_error"] = None
            st.session_state["show_register"] = False
            # Pré-remplir l'email pour le login
            st.session_state["login_email"] = email
        else:
            st.session_state["register_error"] = "Error creating account"
    
    # Si déjà authentifié, retourner True
    if st.session_state.get("authenticated", False):
        return True
    
    
    # ==========================================
    # SÉLECTEUR DE LANGUE EN HAUT
    # ==========================================
    col1, col2, col3 = st.columns([2, 1, 2])
    
    with col2:
        lang_option = st.selectbox(
            "🌍",
            options=["fr", "en"],
            format_func=lambda x: "🇫🇷 Français" if x == "fr" else "🇬🇧 English",
            index=0 if ui_lang == "fr" else 1,
            key="login_lang_selector",
            label_visibility="collapsed"
        )
        
        # Si changement de langue, mettre à jour et rerun
        if lang_option != ui_lang:
            st.session_state["ui_lang"] = lang_option
            st.rerun()
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Recharger les traductions si la langue a changé
    t = texts.get(st.session_state.get("ui_lang", "fr"), texts['fr'])
    
    
    # Styles CSS
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
        .trial-badge {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1rem;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 2rem;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown('<div class="login-container">', unsafe_allow_html=True)
    
    # Header
    st.markdown('<div class="login-header">', unsafe_allow_html=True)
    st.title(t['title'])
    st.markdown(f"**{t['app_name']}**")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Badge essai gratuit
    st.markdown(f"""
    <div class="trial-badge">
        <h3 style="margin: 0; color: white;">{t['trial_badge_title']}</h3>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem;">
            <strong>{t['trial_badge_text']}</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Toggle entre Login et Register
    show_register = st.session_state.get("show_register", False)
    
    if not show_register:
        # ==========================================
        # FORMULAIRE DE CONNEXION
        # ==========================================
        
        # Afficher succès inscription si présent
        if st.session_state.get("register_success"):
            st.success(st.session_state["register_success"])
            st.session_state["register_success"] = None
        
        # Afficher erreur si présente
        if st.session_state.get("auth_error"):
            st.error(f"❌ {st.session_state['auth_error']}")
        
        # Formulaire de connexion
        with st.form("login_form", clear_on_submit=False):
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
            
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                submit = st.form_submit_button(
                    t['login_button'],
                    use_container_width=True,
                    type="primary"
                )
        
        if submit:
            login_submitted()
            if st.session_state.get("authenticated"):
                st.rerun()
        
        st.markdown("---")
        st.markdown(f"<p style='text-align: center;'>{t['or_separator']}</p>", unsafe_allow_html=True)
        
        # Bouton pour aller à l'inscription
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(t['register_button'], use_container_width=True):
                st.session_state["show_register"] = True
                st.session_state["auth_error"] = None
                st.rerun()
    
    else:
        # ==========================================
        # FORMULAIRE D'INSCRIPTION
        # ==========================================
        
        st.markdown(f"### {t['register_title']}")
        st.info(t['register_info'])
        
        # Afficher erreur si présente
        if st.session_state.get("register_error"):
            st.error(f"❌ {st.session_state['register_error']}")
        
        # Formulaire d'inscription
        with st.form("register_form", clear_on_submit=True):
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
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                submit = st.form_submit_button(
                    t['create_account_button'],
                    use_container_width=True,
                    type="primary"
                )
        
        if submit:
            register_submitted()
            if not st.session_state.get("register_error"):
                st.rerun()
        
        st.markdown("---")
        
        # Bouton retour au login
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(t['back_to_login'], use_container_width=True):
                st.session_state["show_register"] = False
                st.session_state["register_error"] = None
                st.rerun()
    
    # Info tarifs
    with st.expander(f"💰 {t['pricing_info']}"):
        st.markdown(f"""
        - 🌱 {t['starter_plan']}
        - 🚀 {t['pro_plan']}
        - 🏢 {t['enterprise_plan']}
        """)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    return False


# ==========================================
# GESTION DES QUOTAS
# ==========================================

def can_generate_report() -> Tuple[bool, str]:
    """
    Vérifie si l'utilisateur peut générer un rapport
    
    Returns:
        (bool, str): (peut_générer, message)
    """
    if not st.session_state.get("authenticated"):
        return False, "Not authenticated"
    
    plan = st.session_state.get("user_plan", "trial")
    used = st.session_state.get("reports_used", 0)
    limit = st.session_state.get("reports_limit", 3)
    
    ui_lang = st.session_state.get("ui_lang", "fr")
    
    # Traductions
    if ui_lang == 'fr':
        msg_remaining = f"Essai gratuit : {limit - used} rapport(s) restant(s)"
        msg_limit_reached = f"Limite mensuelle atteinte ({limit} rapports/mois)"
        msg_trial_expired = "Essai gratuit épuisé"
    else:
        msg_remaining = f"Free trial: {limit - used} report(s) remaining"
        msg_limit_reached = f"Monthly limit reached ({limit} reports/month)"
        msg_trial_expired = "Free trial expired"
    
    # Plan payant
    if plan in ["starter", "pro", "enterprise"]:
        if used < limit:
            return True, ""
        else:
            return False, msg_limit_reached
    
    # Plan trial
    if plan == "trial":
        if used < limit:
            remaining = limit - used
            return True, msg_remaining
        else:
            return False, msg_trial_expired
    
    return False, "Unknown plan"


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
    remaining = max(0, limit - used)
    percentage = (used / limit * 100) if limit > 0 else 0
    
    return {
        "plan": plan,
        "used": used,
        "limit": limit,
        "remaining": remaining,
        "percentage": percentage,
        "is_trial": plan == "trial",
        "is_expired": used >= limit
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
    
    st.markdown("---")
    
    # Traductions
    if ui_lang == 'fr':
        trial_label = "🎁 Essai Gratuit"
        trial_expired = "🚫 Essai gratuit épuisé"
        used_label = "Utilisés"
        remaining_label = "Restants"
        trial_ended = "⚠️ Essai gratuit terminé"
        continue_text = "Continuez à utiliser le service :"
        contact_text = "📧 Contact : agouanetf@yahoo.com"
        pricing_title = "Tarifs :"
        starter = "🌱 29$/mois (100 rapports)"
        pro = "🚀 99$/mois (500 rapports)"
        warning_remaining = f"⚠️ Plus que {quota['remaining']} rapport(s) gratuit(s) !"
        warning_monthly = f"⚠️ Plus que {quota['remaining']} rapport(s) ce mois"
        think_subscribe = "💡 Pensez à vous abonner pour continuer"
    else:
        trial_label = "🎁 Free Trial"
        trial_expired = "🚫 Free trial expired"
        used_label = "Used"
        remaining_label = "Remaining"
        trial_ended = "⚠️ Free trial ended"
        continue_text = "Continue using the service:"
        contact_text = "📧 Contact: agouanetf@yahoo.com"
        pricing_title = "Pricing:"
        starter = "🌱 29$/month (100 reports)"
        pro = "🚀 99$/month (500 reports)"
        warning_remaining = f"⚠️ Only {quota['remaining']} free report(s) left!"
        warning_monthly = f"⚠️ Only {quota['remaining']} report(s) left this month"
        think_subscribe = "💡 Consider subscribing to continue"
    
    if quota["is_trial"]:
        # Badge essai gratuit
        if quota["is_expired"]:
            st.error(trial_expired)
        else:
            st.info(trial_label)
    else:
        plan_labels = {
            "starter": "🌱 Starter",
            "pro": "🚀 Pro",
            "enterprise": "🏢 Enterprise"
        }
        st.success(f"**{plan_labels.get(quota['plan'], quota['plan'])}**")
    
    # Progress bar
    if quota["limit"] > 0:
        st.progress(min(quota["percentage"] / 100, 1.0))
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric(used_label, quota["used"])
    with col2:
        st.metric(remaining_label, quota["remaining"])
    
    # Avertissements
    if quota["is_trial"] and quota["is_expired"]:
        st.error(f"**{trial_ended}**")
        st.markdown(f"""
        **{continue_text}**
        
        {contact_text}
        
        **{pricing_title}**
        - {starter}
        - {pro}
        """)
    
    elif quota["is_trial"] and quota["remaining"] <= 1:
        st.warning(warning_remaining)
        st.info(think_subscribe)
    
    elif not quota["is_trial"] and quota["remaining"] <= 5:
        st.warning(warning_monthly)


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
            
            **🌱 Starter - 29€/mois**
            - ✅ 50 rapports/mois
            - ✅ Export HTML + Word
            - ✅ Support email
            
            **🚀 Pro - 99€/mois** ⭐ Populaire
            - ✅ 200 rapports/mois
            - ✅ Export HTML + Word
            - ✅ Support prioritaire
            - ✅ API access
            
            **🏢 Enterprise - Sur devis**
            - ✅ Rapports illimités
            - ✅ Support dédié
            - ✅ Personnalisation
            
            ---
            
            📧 **Contact** : contact@votreapp.com  
            💬 **Sujet** : Abonnement AI Report Generator
            """)
        else:
            st.markdown("""
            ### 🎉 You've used your 3 free reports!
            
            **Enjoyed the service?** Upgrade to a paid plan to continue:
            
            #### 📋 Our Plans
            
            **🌱 Starter - $29/month**
            - ✅ 50 reports/month
            - ✅ HTML + Word export
            - ✅ Email support
            
            **🚀 Pro - $99/month** ⭐ Popular
            - ✅ 200 reports/month
            - ✅ HTML + Word export
            - ✅ Priority support
            - ✅ API access
            
            **🏢 Enterprise - Custom pricing**
            - ✅ Unlimited reports
            - ✅ Dedicated support
            - ✅ Customization
            
            ---
            
            📧 **Contact**: contact@yourapp.com  
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
            
            📧 **Contact** : contact@votreapp.com
            """)
        else:
            st.markdown(f"""
            ### ⚠️ Monthly limit reached
            
            You've used your **{quota['limit']} reports** for this month.
            
            **Options:**
            - ⏳ Wait for next month
            - 📈 Upgrade to higher plan
            
            📧 **Contact**: contact@yourapp.com
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
