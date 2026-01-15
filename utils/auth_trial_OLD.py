"""
Système d'authentification avec essai gratuit
Version MVP - 3 rapports gratuits puis abonnement requis
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
        # En production, charger depuis une vraie DB
        # Pour MVP, on utilise les secrets Streamlit
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
# AUTHENTIFICATION
# ==========================================

def check_login() -> bool:
    """
    Vérifie l'authentification
    Retourne True si authentifié, False sinon
    """
    
    def login_submitted():
        """Callback quand le formulaire est soumis"""
        email = st.session_state.get("login_email", "").strip().lower()
        password = st.session_state.get("login_password", "")
        
        if not email or not password:
            st.session_state["auth_error"] = "Veuillez remplir tous les champs"
            return
        
        # Récupérer l'utilisateur
        user = get_user(email)
        
        if user and hash_password(password) == user.get("password_hash"):
            # Authentification réussie
            st.session_state["authenticated"] = True
            st.session_state["user_email"] = email
            st.session_state["user_plan"] = user.get("plan", "trial")
            st.session_state["reports_used"] = user.get("reports_used", 0)
            st.session_state["reports_limit"] = user.get("reports_limit", 3)
            st.session_state["auth_error"] = None
        else:
            st.session_state["authenticated"] = False
            st.session_state["auth_error"] = "Email ou mot de passe incorrect"
    
    # Si déjà authentifié, retourner True
    if st.session_state.get("authenticated", False):
        return True
    
    # Afficher la page de login
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
    st.title("🔒 Connexion")
    st.markdown("**AI Report Generator**")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Badge essai gratuit
    st.markdown("""
    <div class="trial-badge">
        <h3 style="margin: 0; color: white;">🎁 Essai Gratuit</h3>
        <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem;">
            <strong>3 rapports offerts</strong> pour tester le service
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Afficher erreur si présente
    if st.session_state.get("auth_error"):
        st.error(f"❌ {st.session_state['auth_error']}")
    
    # Formulaire de connexion
    with st.form("login_form", clear_on_submit=True):
        st.text_input(
            "📧 Email",
            key="login_email",
            placeholder="votre@email.com"
        )
        st.text_input(
            "🔑 Mot de passe",
            type="password",
            key="login_password",
            placeholder="Votre mot de passe"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            submit = st.form_submit_button(
                "Se connecter",
                use_container_width=True,
                type="primary"
            )
        with col2:
            if st.form_submit_button("Créer un compte/create an account", use_container_width=True):
                st.info("📧 Contactez-nous/ Contact us : agouanetf@yahoo.com")
    
    if submit:
        login_submitted()
        if st.session_state.get("authenticated"):
            st.rerun()
    
    st.markdown("---")
    
    # Info nouveau compte
    with st.expander("🆕 Nouveau ? Créez votre compte gratuit \n News? Create your account"):
        st.markdown("""
        **Obtenez votre accès immédiat :**
        
        1. 📧 Envoyez un email à **contact@votreapp.com**
        2. ✅ Recevez vos identifiants
        3. 🎁 **3 rapports gratuits** pour tester
        4. 💳 Abonnez-vous si vous êtes satisfait
        
        **Tarifs après l'essai :**
        - 🌱 Starter : 29$/mois (100 rapports)
        - 🚀 Pro : 50$/mois (200 rapports)
        - 🏢 Enterprise : Sur devis (illimité)
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
        return False, "Non authentifié"
    
    plan = st.session_state.get("user_plan", "trial")
    used = st.session_state.get("reports_used", 0)
    limit = st.session_state.get("reports_limit", 3)
    
    # Plan payant (illimité ou limite haute)
    if plan in ["starter", "pro", "enterprise"]:
        if used < limit:
            return True, ""
        else:
            return False, f"Limite mensuelle atteinte ({limit} rapports/mois)"
    
    # Plan trial (essai gratuit)
    if plan == "trial":
        if used < limit:
            remaining = limit - used
            return True, f"Essai gratuit : {remaining} rapport(s) restant(s)"
        else:
            return False, "Essai gratuit épuisé"
    
    return False, "Plan inconnu"


def increment_report_count():
    """Incrémente le compteur de rapports utilisés"""
    if "reports_used" in st.session_state:
        st.session_state.reports_used += 1
        
        # En production : sauvegarder dans la DB
        # update_user_in_db(st.session_state.user_email, {"reports_used": st.session_state.reports_used})


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
    
    quota = get_quota_info()
    
    st.markdown("---")
    
    if quota["is_trial"]:
        # Badge essai gratuit
        if quota["is_expired"]:
            st.error("🚫 Essai gratuit épuisé")
        else:
            st.info(f"🎁 **Essai Gratuit**")
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
        st.metric("Utilisés", quota["used"])
    with col2:
        st.metric("Restants", quota["remaining"])
    
    # Avertissements
    if quota["is_trial"] and quota["is_expired"]:
        st.error("⚠️ **Essai gratuit terminé**")
        st.markdown("""
        **Continuez à utiliser le service :**
        
        📧 Contact : contact@votreapp.com
        
        **Tarifs :**
        - 🌱 29€/mois (50 rapports)
        - 🚀 99€/mois (200 rapports)
        """)
    
    elif quota["is_trial"] and quota["remaining"] <= 1:
        st.warning(f"⚠️ Plus que {quota['remaining']} rapport(s) gratuit(s) !")
        st.info("💡 Pensez à vous abonner pour continuer")
    
    elif not quota["is_trial"] and quota["remaining"] <= 5:
        st.warning(f"⚠️ Plus que {quota['remaining']} rapport(s) ce mois")


def show_upgrade_message():
    """Affiche le message pour passer à un plan payant"""
    st.error("🚫 **Limite atteinte**")
    
    quota = get_quota_info()
    
    if quota["is_trial"]:
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
        st.markdown(f"""
        ### ⚠️ Limite mensuelle atteinte
        
        Vous avez utilisé vos **{quota['limit']} rapports** de ce mois.
        
        **Options :**
        - ⏳ Attendez le mois prochain
        - 📈 Passez au plan supérieur
        
        📧 **Contact** : contact@votreapp.com
        """)


def logout():
    """Déconnexion"""
    keys_to_delete = [
        "authenticated", "user_email", "user_plan", 
        "reports_used", "reports_limit", "auth_error"
    ]
    for key in keys_to_delete:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()