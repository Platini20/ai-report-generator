"""
Authentification via Supabase Auth (natif)
Remplace auth_trial.py.

Les noms de fonctions publiques sont IDENTIQUES à l'ancien module
(check_login, can_generate_report, increment_report_count,
show_quota_sidebar, show_upgrade_message, logout) pour que app.py
n'ait qu'UNE seule ligne à changer : l'import.

Les plans sont importés depuis plans_config.py (source unique).
"""

import streamlit as st
from datetime import datetime
from typing import Dict, Optional, Tuple

from supabase import create_client, Client

from utils.plans_config import PLAN_CONFIGS, DEFAULT_PLAN, get_plan

CONTACT_EMAIL = "agouanetf@yahoo.com"


# ==========================================
# CLIENTS SUPABASE
# ==========================================

@st.cache_resource
def get_auth_client() -> Client:
    """Client Supabase (clé anon) — utilisé UNIQUEMENT pour les opérations
    d'authentification (sign_up / sign_in / sign_out)."""
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"])


@st.cache_resource
def get_admin_client() -> Client:
    """Client Supabase (clé service_role) — bypass les règles RLS.
    Sûr à utiliser ici car ce code tourne côté serveur Streamlit,
    jamais exposé au navigateur de l'utilisateur.
    Ne JAMAIS importer ce client dans du code qui s'exécute côté client."""
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_SERVICE_KEY"])


def get_profile(user_id: str) -> Optional[Dict]:
    """Récupère le profil (plan, quota, Stripe) d'un utilisateur."""
    try:
        res = get_admin_client().table("profiles").select("*").eq("id", user_id).single().execute()
        return res.data
    except Exception:
        return None


def update_profile(user_id: str, fields: Dict) -> None:
    """Met à jour le profil d'un utilisateur (quota, plan, Stripe, etc.)."""
    fields = {**fields, "updated_at": datetime.utcnow().isoformat()}
    try:
        get_admin_client().table("profiles").update(fields).eq("id", user_id).execute()
    except Exception as e:
        st.warning(f"⚠️ Synchronisation profil échouée (non bloquant) : {e}")


def request_password_reset(email: str) -> Tuple[bool, str]:
    """Envoie un email de réinitialisation de mot de passe."""
    try:
        app_url = st.secrets["APP_URL"].rstrip("/")
        get_auth_client().auth.reset_password_for_email(
            email, {"redirect_to": app_url}
        )
        return True, ""
    except Exception as e:
        return False, str(e)


def handle_password_recovery() -> bool:
    """
    À appeler tout en haut de app.py, AVANT check_login().
    Si l'URL contient ?type=recovery&token_hash=..., vérifie le lien
    UNE SEULE FOIS (les liens sont à usage unique), stocke la session
    obtenue, puis affiche le formulaire de nouveau mot de passe.
    Les réessais (ex: mot de passe identique refusé) réutilisent cette
    session déjà établie au lieu de re-vérifier le lien.
    Retourne True si le script principal doit s'arrêter (st.stop()).
    """
    ui_lang = st.session_state.get("ui_lang", "en")

    # Session de récupération déjà établie : afficher directement le formulaire
    if st.session_state.get("recovery_active"):
        return _render_recovery_form(ui_lang)

    params = st.query_params
    if params.get("type") != "recovery" or "token_hash" not in params:
        return False

    token_hash = params["token_hash"]
    client = get_auth_client()

    try:
        result = client.auth.verify_otp({"token_hash": token_hash, "type": "recovery"})
    except Exception:
        result = None

    st.query_params.clear()  # le lien ne doit plus jamais être réutilisé

    if not result or not result.session:
        st.error(
            "Lien invalide ou expiré. Redemandez un lien depuis l'écran de connexion."
            if ui_lang == "fr"
            else "Invalid or expired link. Request a new one from the login screen."
        )
        return True

    # Token consommé UNE FOIS ici — la session est conservée pour les réessais
    st.session_state["recovery_access_token"] = result.session.access_token
    st.session_state["recovery_refresh_token"] = result.session.refresh_token
    st.session_state["recovery_active"] = True

    return _render_recovery_form(ui_lang)


def _render_recovery_form(ui_lang: str) -> bool:
    """Affiche le formulaire de nouveau mot de passe, en réutilisant la
    session de récupération déjà établie (pas de re-vérification du lien)."""
    _language_switcher()

    st.markdown("## 🔑 " + ("Nouveau mot de passe" if ui_lang == "fr" else "New password"))
    st.caption(
        "Choisissez un nouveau mot de passe pour votre compte."
        if ui_lang == "fr"
        else "Choose a new password for your account."
    )

    with st.form("reset_password_form"):
        new_password = st.text_input(
            "Nouveau mot de passe" if ui_lang == "fr" else "New password", type="password"
        )
        confirm_password = st.text_input(
            "Confirmer le mot de passe" if ui_lang == "fr" else "Confirm password", type="password"
        )
        submitted = st.form_submit_button(
            "Valider" if ui_lang == "fr" else "Submit", type="primary"
        )

    if submitted:
        if len(new_password) < 6:
            st.error(
                "Le mot de passe doit contenir au moins 6 caractères"
                if ui_lang == "fr" else "Password must be at least 6 characters"
            )
        elif new_password != confirm_password:
            st.error(
                "Les mots de passe ne correspondent pas"
                if ui_lang == "fr" else "Passwords do not match"
            )
        else:
            try:
                client = get_auth_client()
                client.auth.set_session(
                    st.session_state["recovery_access_token"],
                    st.session_state["recovery_refresh_token"],
                )
                client.auth.update_user({"password": new_password})
                client.auth.sign_out()

                for key in ["recovery_active", "recovery_access_token", "recovery_refresh_token"]:
                    st.session_state.pop(key, None)

                st.success(
                    "✅ Mot de passe mis à jour avec succès !"
                    if ui_lang == "fr" else "✅ Password updated successfully!"
                )
                if st.button("Aller à la connexion" if ui_lang == "fr" else "Go to login"):
                    st.rerun()
            except Exception as e:
                # Session de récupération conservée : l'utilisateur peut réessayer
                # (ex: "New password should be different from the old password")
                st.error(f"Erreur : {e}")

    return True


def _language_switcher():
    """Petit sélecteur de langue, utilisable AVANT connexion (login, register,
    mot de passe oublié, reset de mot de passe)."""
    current = st.session_state.get("ui_lang", "en")
    col1, col2 = st.columns([3, 1])
    with col2:
        new_lang = st.selectbox(
            "🌍",
            options=["en", "fr"],
            format_func=lambda x: "🇬🇧 EN" if x == "en" else "🇫🇷 FR",
            index=0 if current == "en" else 1,
            key="lang_switcher_pre_auth",
            label_visibility="collapsed",
        )
    if new_lang != current:
        st.session_state["ui_lang"] = new_lang
        st.rerun()


# ==========================================
# AUTHENTIFICATION (UI)
# ==========================================

def check_login() -> bool:
    """
    Affiche le formulaire de connexion/inscription si nécessaire.
    Retourne True si l'utilisateur est authentifié.
    """
    ui_lang = st.session_state.get("ui_lang", "en")

    texts = {
        'fr': {
            'title': '🔒 Connexion',
            'app_name': 'AI Report Generator',
            'trial_badge_title': '🎁 Essai Gratuit',
            'trial_badge_text': '3 rapports offerts pour tester le service — un jeu de données d\'exemple est inclus, pas besoin de fichier à vous pour découvrir l\'app',
            'email_label': '📧 Email',
            'email_placeholder': 'votre@email.com',
            'password_label': '🔑 Mot de passe',
            'password_placeholder': 'Votre mot de passe',
            'login_button': 'Se connecter',
            'register_button': 'Créer un compte',
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
            'error_email_not_confirmed': 'Veuillez confirmer votre email avant de vous connecter (vérifiez votre boîte de réception)',
            'success_account_created': '✅ Compte créé ! Vérifiez votre boîte mail pour confirmer votre adresse avant de vous connecter.',
            'pricing_info': 'Tarifs après l\'essai',
            'pro_plan': 'Pro : 19,99$/mois (300 rapports)',
            'enterprise_plan': 'Enterprise : Sur devis (illimité)',
            'forgot_password': 'Mot de passe oublié ?',
            'forgot_password_title': '🔑 Réinitialiser le mot de passe',
            'forgot_password_info': 'Entrez votre email, vous recevrez un lien pour choisir un nouveau mot de passe.',
            'send_reset_link': 'Envoyer le lien',
            'reset_email_sent': '✅ Email envoyé ! Vérifiez votre boîte de réception (et vos spams).',
        },
        'en': {
            'title': '🔒 Login',
            'app_name': 'AI Report Generator',
            'trial_badge_title': '🎁 Free Trial',
            'trial_badge_text': '3 free reports to test the service — a sample dataset is included, no file of your own needed to try the app',
            'email_label': '📧 Email',
            'email_placeholder': 'your@email.com',
            'password_label': '🔑 Password',
            'password_placeholder': 'Your password',
            'login_button': 'Sign in',
            'register_button': 'Create account',
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
            'error_email_not_confirmed': 'Please confirm your email before signing in (check your inbox)',
            'success_account_created': '✅ Account created! Check your inbox to confirm your address before signing in.',
            'pricing_info': 'Pricing after trial',
            'pro_plan': 'Pro: $19.99/month (300 reports)',
            'enterprise_plan': 'Enterprise: Custom pricing (unlimited)',
            'forgot_password': 'Forgot your password?',
            'forgot_password_title': '🔑 Reset password',
            'forgot_password_info': 'Enter your email, you will receive a link to choose a new password.',
            'send_reset_link': 'Send reset link',
            'reset_email_sent': '✅ Email sent! Check your inbox (and spam folder).',
        }
    }
    t = texts.get(ui_lang, texts['en'])

    def _load_session_into_state(user, session, profile):
        st.session_state["authenticated"] = True
        st.session_state["user_id"] = user.id
        st.session_state["user_email"] = user.email
        st.session_state["access_token"] = session.access_token
        st.session_state["refresh_token"] = session.refresh_token
        st.session_state["user_plan"] = profile["plan"]
        st.session_state["reports_used"] = profile["reports_used"]
        st.session_state["reports_limit"] = profile["reports_limit"]
        st.session_state["auth_error"] = None
        st.session_state["show_register"] = False

    def login_submitted():
        email = st.session_state.get("login_email", "").strip().lower()
        password = st.session_state.get("login_password", "")

        if not email or not password:
            st.session_state["auth_error"] = t['error_empty_fields']
            return

        try:
            result = get_auth_client().auth.sign_in_with_password(
                {"email": email, "password": password}
            )
        except Exception as e:
            msg = str(e).lower()
            if "confirm" in msg:
                st.session_state["auth_error"] = t['error_email_not_confirmed']
            else:
                st.session_state["auth_error"] = t['error_login_failed']
            return

        if not result.user or not result.session:
            st.session_state["auth_error"] = t['error_login_failed']
            return

        profile = get_profile(result.user.id)
        if not profile:
            # Filet de sécurité si le trigger SQL n'a pas encore créé le profil
            get_admin_client().table("profiles").insert({
                "id": result.user.id,
                "email": email,
                "plan": DEFAULT_PLAN,
                "reports_used": 0,
                "reports_limit": PLAN_CONFIGS[DEFAULT_PLAN]["reports_limit"],
            }).execute()
            profile = get_profile(result.user.id)

        _load_session_into_state(result.user, result.session, profile)

    def register_submitted():
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

        try:
            result = get_auth_client().auth.sign_up({"email": email, "password": password})
        except Exception as e:
            msg = str(e).lower()
            if "already" in msg or "exists" in msg:
                st.session_state["register_error"] = t['error_user_exists']
            else:
                st.session_state["register_error"] = str(e)
            return

        if result.user:
            st.session_state["register_success"] = True
            st.session_state["register_error"] = None
        else:
            st.session_state["register_error"] = t['error_login_failed']

    # Déjà authentifié
    if st.session_state.get("authenticated"):
        return True

    _language_switcher()

    st.markdown("""
        <style>
            .login-container { max-width: 500px; margin: 0 auto; padding: 2rem; }
            .login-header { text-align: center; margin-bottom: 2rem; }
            .login-title {
                font-size: 2.5rem; font-weight: 800;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                -webkit-background-clip: text; -webkit-text-fill-color: transparent;
                margin-bottom: 0.5rem;
            }
            .trial-badge {
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                color: white; padding: 0.8rem 1.5rem; border-radius: 12px;
                margin: 1.5rem 0; text-align: center;
                box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
            }
            .pricing-box { background: #f8f9fa; padding: 1rem; border-radius: 8px; margin: 1rem 0; font-size: 0.9rem; }
        </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="login-container">', unsafe_allow_html=True)
        st.markdown(f"""
            <div class="login-header">
                <h1 class="login-title">{t['app_name']}</h1>
                <p style="font-size: 1.1rem; color: #6b7280;">{t['title']}</p>
            </div>
        """, unsafe_allow_html=True)
        st.markdown(f"""
            <div class="trial-badge">
                <div style="font-size: 1.5rem; font-weight: 700; margin-bottom: 0.3rem;">{t['trial_badge_title']}</div>
                <div style="font-size: 0.95rem; opacity: 0.95;">{t['trial_badge_text']}</div>
            </div>
        """, unsafe_allow_html=True)

        show_register = st.session_state.get("show_register", False)
        show_forgot = st.session_state.get("show_forgot_password", False)

        if show_forgot:
            st.markdown(f"### {t['forgot_password_title']}")
            st.info(t['forgot_password_info'])

            if st.session_state.get("reset_email_sent"):
                st.success(t['reset_email_sent'])
                if st.button(t['back_to_login'], use_container_width=True):
                    st.session_state["show_forgot_password"] = False
                    st.session_state["reset_email_sent"] = False
                    st.rerun()
            else:
                st.text_input(t['email_label'], key="forgot_email", placeholder=t['email_placeholder'])
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(t['send_reset_link'], type="primary", use_container_width=True):
                        email = st.session_state.get("forgot_email", "").strip().lower()
                        if email:
                            ok, err = request_password_reset(email)
                            if ok:
                                st.session_state["reset_email_sent"] = True
                                st.rerun()
                            else:
                                st.error(err)
                with col2:
                    if st.button(t['back_to_login'], use_container_width=True):
                        st.session_state["show_forgot_password"] = False
                        st.rerun()

        elif show_register:
            st.markdown(f"### {t['register_title']}")
            st.info(t['register_info'])

            if st.session_state.get("register_success"):
                st.success(t['success_account_created'])
                if st.button(t['back_to_login'], use_container_width=True):
                    st.session_state["show_register"] = False
                    st.session_state["register_success"] = False
                    st.rerun()
            else:
                if st.session_state.get("register_error"):
                    st.error(st.session_state["register_error"])

                st.text_input(t['email_label'], key="register_email", placeholder=t['email_placeholder'])
                st.text_input(t['password_label'], type="password", key="register_password", placeholder=t['password_placeholder'])
                st.text_input(t['confirm_password_label'], type="password", key="register_confirm", placeholder=t['confirm_password_placeholder'])

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
            if st.session_state.get("auth_error"):
                st.error(st.session_state["auth_error"])

            st.text_input(t['email_label'], key="login_email", placeholder=t['email_placeholder'])
            st.text_input(t['password_label'], type="password", key="login_password", placeholder=t['password_placeholder'])

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

            if st.button(t['forgot_password'], use_container_width=True):
                st.session_state["show_forgot_password"] = True
                st.rerun()

        st.markdown("---")
        st.markdown(f"""
            <div class="pricing-box">
                <strong>{t['pricing_info']}</strong><br/>
                🚀 {t['pro_plan']}<br/>
                💎 {t['enterprise_plan']}
            </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

    return False


# ==========================================
# GESTION DES QUOTAS
# ==========================================

def can_generate_report() -> Tuple[bool, str]:
    if not st.session_state.get("authenticated"):
        return False, "Non authentifié"

    plan = st.session_state.get("user_plan", DEFAULT_PLAN)
    reports_used = st.session_state.get("reports_used", 0)
    reports_limit = st.session_state.get("reports_limit", 3)

    if reports_limit == -1:
        return True, ""

    if reports_used >= reports_limit:
        if plan == "trial":
            return False, "Essai gratuit épuisé"
        return False, f"Limite mensuelle atteinte ({reports_limit} rapports)"

    return True, ""


def increment_report_count():
    """Incrémente le compteur en session ET le persiste dans Supabase."""
    if "reports_used" in st.session_state:
        st.session_state.reports_used += 1
        user_id = st.session_state.get("user_id")
        if user_id:
            update_profile(user_id, {"reports_used": st.session_state.reports_used})


def get_quota_info() -> Dict:
    plan = st.session_state.get("user_plan", DEFAULT_PLAN)
    used = st.session_state.get("reports_used", 0)
    limit = st.session_state.get("reports_limit", 3)

    if limit == -1:
        remaining = -1
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
        "is_expired": used >= limit if limit != -1 else False,
    }


# ==========================================
# UI HELPERS
# ==========================================

def show_quota_sidebar():
    if not st.session_state.get("authenticated"):
        return

    ui_lang = st.session_state.get("ui_lang", "en")
    quota = get_quota_info()
    plan_config = get_plan(quota["plan"])

    st.markdown("---")

    if ui_lang == 'fr':
        used_label, remaining_label = "Utilisés", "Restants"
        trial_ended = "⚠️ Essai gratuit terminé"
        continue_text = "Continuez à utiliser le service :"
        contact_text = f"📧 Contact : {CONTACT_EMAIL}"
        pricing_title = "Tarifs :"
        warning_remaining_trial = f"⚠️ Plus que {quota['remaining']} rapport(s) gratuit(s) !"
        warning_remaining_paid = f"⚠️ Plus que {quota['remaining']} rapport(s) ce mois"
        think_subscribe = "💡 Pensez à vous abonner pour continuer"
        unlimited = "Illimité ♾️"
    else:
        used_label, remaining_label = "Used", "Remaining"
        trial_ended = "⚠️ Free trial ended"
        continue_text = "Continue using the service:"
        contact_text = f"📧 Contact: {CONTACT_EMAIL}"
        pricing_title = "Pricing:"
        warning_remaining_trial = f"⚠️ Only {quota['remaining']} free report(s) left!"
        warning_remaining_paid = f"⚠️ Only {quota['remaining']} report(s) left this month"
        think_subscribe = "💡 Consider subscribing to continue"
        unlimited = "Unlimited ♾️"

    plan_display = f"{plan_config['icon']} {plan_config['name']}"

    if quota["is_trial"]:
        st.error(f"🚫 {plan_display}") if quota["is_expired"] else st.info(f"🎁 {plan_display}")
    else:
        st.success(f"{plan_config['icon']} {plan_display}")

    if quota["limit"] > 0:
        st.progress(min(quota["percentage"] / 100, 1.0))

    col1, col2 = st.columns(2)
    with col1:
        st.metric(used_label, quota["used"])
    with col2:
        st.metric(remaining_label, unlimited if quota["limit"] == -1 else quota["remaining"])

    if quota["is_trial"] and quota["is_expired"]:
        st.error(f"**{trial_ended}**")
        st.markdown(f"""
        **{continue_text}**

        {contact_text}

        **{pricing_title}**
        - 🚀 Pro: 19,99$/mois (300 rapports)
        - 💎 Enterprise: Sur devis (illimité)
        """)
    elif quota["is_trial"] and quota["remaining"] <= 1:
        st.warning(warning_remaining_trial)
        st.info(think_subscribe)
    elif not quota["is_trial"] and quota["limit"] != -1 and quota["remaining"] <= 5:
        st.warning(warning_remaining_paid)


def show_upgrade_message():
    ui_lang = st.session_state.get("ui_lang", "en")
    quota = get_quota_info()

    st.error("🚫 **" + ("Limite atteinte" if ui_lang == 'fr' else "Limit reached") + "**")

    if quota["is_trial"]:
        if ui_lang == 'fr':
            st.markdown(f"""
            ### 🎉 Vous avez utilisé vos 3 rapports gratuits !

            **Le service vous plaît ?** Passez à un plan payant pour continuer :

            **🚀 Pro - 19,99$/mois**
            - ✅ 300 rapports/mois
            - ✅ 200 MB max par fichier
            - ✅ 300,000 lignes max
            - ✅ Export HTML + Word + PDF

            **💎 Enterprise - Sur devis**
            - ✅ Rapports illimités
            - ✅ Fichiers et lignes illimités
            - ✅ Support dédié

            ---
            📧 **Contact** : {CONTACT_EMAIL}
            """)
        else:
            st.markdown(f"""
            ### 🎉 You've used your 3 free reports!

            **🚀 Pro - $19.99/month**
            - ✅ 300 reports/month
            - ✅ 200 MB max per file
            - ✅ 300,000 rows max
            - ✅ HTML + Word + PDF export

            **💎 Enterprise - Custom pricing**
            - ✅ Unlimited everything
            - ✅ Dedicated support

            ---
            📧 **Contact**: {CONTACT_EMAIL}
            """)
    else:
        if ui_lang == 'fr':
            st.markdown(f"""
            ### ⚠️ Limite mensuelle atteinte
            Vous avez utilisé vos **{quota['limit']} rapports** de ce mois.
            📧 **Contact** : {CONTACT_EMAIL}
            """)
        else:
            st.markdown(f"""
            ### ⚠️ Monthly limit reached
            You've used your **{quota['limit']} reports** for this month.
            📧 **Contact**: {CONTACT_EMAIL}
            """)


def logout():
    try:
        get_auth_client().auth.sign_out()
    except Exception:
        pass

    keys_to_delete = [
        "authenticated", "user_id", "user_email", "access_token", "refresh_token",
        "user_plan", "reports_used", "reports_limit", "auth_error",
        "register_error", "register_success", "show_register",
        "show_forgot_password", "reset_email_sent", "forgot_email",
        "show_upgrade_success",
        "recovery_active", "recovery_access_token", "recovery_refresh_token",
    ]
    for key in keys_to_delete:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()
