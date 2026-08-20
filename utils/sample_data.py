"""
Génère un dataset d'exemple synthétique (ventes trimestrielles d'un
commerce) pour permettre de tester l'app sans avoir de fichier sous la
main. Inclut volontairement quelques valeurs manquantes et doublons
pour que les fonctionnalités de détection d'anomalies aient aussi
quelque chose à montrer.
"""

import io
import numpy as np
import pandas as pd

EXAMPLE_FILENAME_FR = "exemple_ventes_trimestrielles.csv"
EXAMPLE_FILENAME_EN = "example_quarterly_sales.csv"


def generate_sample_dataframe(seed: int = 42) -> pd.DataFrame:
    """Génère un dataset synthétique de ventes trimestrielles."""
    rng = np.random.default_rng(seed)
    n = 400

    dates = pd.date_range("2025-01-01", "2025-12-31", periods=n)

    regions = rng.choice(
        ["Nord", "Sud", "Est", "Ouest", "Centre"],
        size=n, p=[0.25, 0.2, 0.2, 0.15, 0.2]
    )
    categories = rng.choice(
        ["Électronique", "Vêtements", "Maison", "Sport", "Alimentation"],
        size=n
    )
    canaux = rng.choice(["En ligne", "Magasin", "Téléphone"], size=n, p=[0.55, 0.4, 0.05])

    quantite = rng.integers(1, 25, size=n)
    prix_unitaire = np.round(rng.uniform(8, 350, size=n), 2)
    revenu = np.round(quantite * prix_unitaire, 2)

    # Satisfaction client (1-5), avec un peu de bruit et une corrélation
    # légère avec le canal (en ligne un peu moins bien noté, volontairement)
    base_satisfaction = rng.normal(4.0, 0.8, size=n)
    canal_penalty = np.where(canaux == "En ligne", -0.3, 0.0)
    satisfaction = np.clip(np.round(base_satisfaction + canal_penalty, 1), 1, 5)

    df = pd.DataFrame({
        "date": dates,
        "region": regions,
        "categorie_produit": categories,
        "canal_vente": canaux,
        "quantite": quantite,
        "prix_unitaire": prix_unitaire,
        "revenu": revenu,
        "satisfaction_client": satisfaction,
        "id_transaction": [f"TX-{10000 + i}" for i in range(n)],
    })

    # Quelques valeurs manquantes volontaires (réalisme + démo anomalies)
    missing_idx = rng.choice(n, size=int(n * 0.08), replace=False)
    df.loc[missing_idx, "satisfaction_client"] = np.nan

    missing_idx2 = rng.choice(n, size=int(n * 0.03), replace=False)
    df.loc[missing_idx2, "region"] = np.nan

    # Une colonne quasi-vide, pour démontrer la détection d'anomalies
    df["code_promo_special"] = pd.Series([np.nan] * n, dtype="object")
    promo_idx = rng.choice(n, size=int(n * 0.05), replace=False)
    df.loc[promo_idx, "code_promo_special"] = "PROMO2025"

    # Quelques doublons volontaires
    dup_rows = df.sample(n=8, random_state=seed)
    df = pd.concat([df, dup_rows], ignore_index=True)

    # Un léger outlier de revenu pour la démo de détection de valeurs aberrantes
    df.loc[df.index[-1], "revenu"] = df["revenu"].max() * 6

    return df


def get_example_file(lang: str = "fr") -> io.BytesIO:
    """
    Retourne un objet fichier en mémoire (avec .name), directement
    utilisable par load_file()/load_any_file() comme s'il s'agissait
    d'un vrai fichier uploadé par l'utilisateur.
    """
    df = generate_sample_dataframe()
    buffer = io.BytesIO()
    df.to_csv(buffer, index=False)
    buffer.seek(0)
    buffer.name = EXAMPLE_FILENAME_FR if lang == "fr" else EXAMPLE_FILENAME_EN
    return buffer
