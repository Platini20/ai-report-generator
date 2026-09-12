"""
Suivi du quota d'essai gratuit pour les utilisateurs NON connectés.

Utilise un identifiant stocké dans le localStorage du navigateur (survit
à la fermeture de l'onglet et au rafraîchissement, contrairement à
st.session_state) + la table Supabase "anonymous_trials" pour la
persistance réelle du compteur.

⚠️ Contournable en vidant le cache navigateur ou en navigation privée —
c'est un compromis assumé pour réduire la friction d'essai (pas de
compte requis pour tester l'app), pas une protection anti-abus absolue.
Voir IMPLEMENTATION_GUIDE.md.

Dépendance : streamlit-local-storage (ajoutée à requirements.txt)
"""

import uuid
import streamlit as st
from datetime import datetime
from typing import Optional, Dict

from streamlit_local_storage import LocalStorage

from utils.auth_supabase import get_admin_client
from utils.plans_config import PLAN_CONFIGS

_local_storage: Optional[LocalStorage] = None
_DEVICE_ID_KEY = "ai_report_gen_device_id"


def _get_local_storage() -> LocalStorage:
    """Initialise LocalStorage seulement lorsqu'une session Streamlit existe."""
    global _local_storage

    if _local_storage is None:
        _local_storage = LocalStorage()

    return _local_storage


def get_device_id() -> Optional[str]:
    """
    Récupère (ou crée) un identifiant persistant dans le localStorage
    du navigateur.

    Retourne None le temps que le composant JS se charge (typiquement
    le tout premier rendu de la page) — l'appelant doit gérer ce cas
    (afficher un message d'attente et laisser Streamlit re-render).
    """
    local_storage = _get_local_storage()
    existing = local_storage.getItem(_DEVICE_ID_KEY)

    if existing:
        return existing

    # Pas encore de valeur en localStorage : on en crée une et on la
    # pousse au navigateur. Elle ne sera lisible qu'au prochain rerun.
    if "_pending_device_id" not in st.session_state:
        st.session_state["_pending_device_id"] = str(uuid.uuid4())
        local_storage.setItem(
            _DEVICE_ID_KEY,
            st.session_state["_pending_device_id"],
        )

    return None


def get_or_create_anon_trial(device_id: str) -> Dict:
    """Récupère la ligne d'essai anonyme pour cet appareil, la crée si absente."""
    admin = get_admin_client()
    res = admin.table("anonymous_trials").select("*").eq("device_id", device_id).execute()

    if res.data:
        return res.data[0]

    default_limit = PLAN_CONFIGS["trial"]["reports_limit"]
    admin.table("anonymous_trials").insert({
        "device_id": device_id,
        "reports_used": 0,
        "reports_limit": default_limit,
    }).execute()

    return {"device_id": device_id, "reports_used": 0, "reports_limit": default_limit}


def increment_anon_report_count(device_id: str, new_count: int) -> None:
    """Persiste le nouveau compteur de rapports pour cet appareil anonyme."""
    admin = get_admin_client()
    try:
        admin.table("anonymous_trials").update({
            "reports_used": new_count,
            "updated_at": datetime.utcnow().isoformat(),
        }).eq("device_id", device_id).execute()
    except Exception:
        pass  # Non bloquant : le compteur reste correct en session pour cette visite
