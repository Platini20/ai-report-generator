"""
Intégration Stripe Checkout (Phase 2)
Gère la création de session de paiement et la mise à jour du profil
Supabase quand l'utilisateur revient sur l'app après un paiement réussi.

⚠️ Ceci couvre le flux "achat immédiat". Les événements asynchrones
(échec de paiement, annulation en cours de mois, renouvellement) ne
sont PAS couverts ici — ils nécessitent le webhook Stripe (Phase 3),
car ils peuvent survenir alors que l'utilisateur n'est pas dans l'app.
"""

import streamlit as st
import stripe

from utils.auth_supabase import update_profile, get_profile
from utils.plans_config import PLAN_CONFIGS

stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]


def create_checkout_session(user_id: str, email: str) -> str:
    """Crée une session Stripe Checkout et retourne l'URL de paiement à ouvrir."""
    app_url = st.secrets["APP_URL"].rstrip("/")

    session = stripe.checkout.Session.create(
        mode="subscription",
        payment_method_types=["card"],
        line_items=[{"price": st.secrets["STRIPE_PRICE_ID_PRO"], "quantity": 1}],
        customer_email=email,
        client_reference_id=user_id,
        success_url=f"{app_url}/?checkout=success&session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{app_url}/?checkout=cancel",
        metadata={"user_id": user_id},
    )
    return session.url


def handle_checkout_return():
    """
    À appeler juste après check_login() dans app.py, à chaque run.
    Si l'URL contient ?checkout=success&session_id=..., vérifie le
    paiement auprès de Stripe et passe l'utilisateur en plan Pro.
    """
    params = st.query_params

    if params.get("checkout") == "cancel":
        st.info(
            "Paiement annulé — vous restez sur votre plan actuel."
            if st.session_state.get("ui_lang", "fr") == "fr"
            else "Payment canceled — you remain on your current plan."
        )
        st.query_params.clear()
        return

    if params.get("checkout") == "success" and "session_id" in params:
        session_id = params["session_id"]
        try:
            session = stripe.checkout.Session.retrieve(session_id, expand=["subscription"])
        except Exception as e:
            st.error(f"Erreur de vérification du paiement Stripe : {e}")
            st.query_params.clear()
            return

        if session.payment_status == "paid":
            user_id = session.client_reference_id
            subscription = session.subscription
            subscription_id = subscription.id if subscription else None
            plan_config = PLAN_CONFIGS["pro"]

            update_profile(user_id, {
                "plan": "pro",
                "reports_used": 0,
                "reports_limit": plan_config["reports_limit"],
                "stripe_customer_id": session.customer,
                "stripe_subscription_id": subscription_id,
                "subscription_status": "active",
            })

            # Synchronise la session en cours si c'est le même utilisateur
            if st.session_state.get("user_id") == user_id:
                st.session_state["user_plan"] = "pro"
                st.session_state["reports_used"] = 0
                st.session_state["reports_limit"] = plan_config["reports_limit"]
                st.session_state["show_upgrade_success"] = True
        else:
            st.warning(
                "Paiement non confirmé par Stripe pour le moment."
                if st.session_state.get("ui_lang", "fr") == "fr"
                else "Payment not yet confirmed by Stripe."
            )

        st.query_params.clear()
        st.rerun()


def create_portal_session(customer_id: str) -> str:
    """Crée une session Stripe Customer Portal et retourne son URL."""
    app_url = st.secrets["APP_URL"].rstrip("/")
    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=f"{app_url}/",
    )
    return session.url


def show_manage_subscription_button():
    """
    Affiche un bouton 'Gérer mon abonnement' pour les utilisateurs Pro,
    qui ouvre le Stripe Customer Portal (annulation, moyen de paiement,
    factures — tout géré par Stripe, rien à coder côté app).
    """
    if st.session_state.get("user_plan") != "pro":
        return

    ui_lang = st.session_state.get("ui_lang", "fr")
    label = "⚙️ Gérer mon abonnement" if ui_lang == "fr" else "⚙️ Manage subscription"

    if st.button(label, use_container_width=True):
        try:
            profile = get_profile(st.session_state["user_id"])
            customer_id = profile.get("stripe_customer_id") if profile else None
            if not customer_id:
                st.error(
                    "Aucun abonnement Stripe trouvé pour ce compte."
                    if ui_lang == "fr"
                    else "No Stripe subscription found for this account."
                )
                return
            portal_url = create_portal_session(customer_id)
            st.link_button(
                "👉 Ouvrir le portail de gestion" if ui_lang == "fr" else "👉 Open management portal",
                portal_url,
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Erreur Stripe : {e}")


def show_upgrade_button():
    """
    Affiche le bouton 'Passer Pro' dans la sidebar si l'utilisateur
    est en plan Trial. À appeler juste après show_quota_sidebar().
    """
    if st.session_state.get("user_plan") != "trial":
        return

    ui_lang = st.session_state.get("ui_lang", "fr")
    label = "🚀 Passer Pro — 19,99$/mois" if ui_lang == "fr" else "🚀 Upgrade to Pro — $19.99/mo"

    if st.button(label, type="primary", use_container_width=True):
        try:
            checkout_url = create_checkout_session(
                user_id=st.session_state["user_id"],
                email=st.session_state["user_email"],
            )
            st.link_button(
                "👉 Continuer vers le paiement" if ui_lang == "fr" else "👉 Continue to payment",
                checkout_url,
                use_container_width=True,
            )
        except Exception as e:
            st.error(f"Erreur Stripe : {e}")
