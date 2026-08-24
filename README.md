# 📊 Générateur de Rapports IA / AI Report Generator

Application web SaaS qui génère automatiquement des rapports d'analyse de données avec insights IA, à partir de fichiers CSV, Excel, JSON ou Parquet.

Professional SaaS web app that automatically generates data analysis reports with AI insights, from CSV, Excel, JSON, or Parquet files.

🔗 **App en ligne** : `https://ai-report-generator-franklin2026-ajjj.streamlit.app`

---

## ✨ Fonctionnalités

- **📁 Multi-format** : CSV, Excel (.xlsx, .xls), JSON, Parquet
- **🧹 Nettoyage automatique** des données + score de qualité
- **📊 Analyse statistique complète** (moyennes, quartiles, détection d'anomalies)
- **📈 Visualisations** : sélection IA des graphiques "coup de cœur" + vue exhaustive (selon plan)
- **🧠 Insights IA** propulsés par Claude (Anthropic), avec repli automatique en mode basique si l'API échoue (sans jamais décompter le quota dans ce cas)
- **💬 Chat conversationnel** : posez des questions de suivi sur un rapport déjà généré
- **🎯 Dataset d'exemple intégré** : découvrez l'app sans avoir à uploader vos propres données
- **📄 Export** : HTML (imprimable en PDF via le navigateur) + Word (.docx, plans payants)
- **🌍 Interface bilingue** FR/EN (anglais par défaut)
- **🔒 Authentification** sécurisée (Supabase Auth), mot de passe oublié inclus
- **💳 Abonnements** gérés via Stripe (Checkout + portail de gestion self-service)

## 💰 Plans

| | 🎁 Trial | 🚀 Pro | 💎 Enterprise |
|---|---|---|---|
| Prix | Gratuit | 19,99$/mois | Sur devis |
| Rapports | 3 (à vie) | 300/mois | Illimité |
| Fichier max | 10 MB / 5 000 lignes | 200 MB / 300 000 lignes | Illimité |
| Export | HTML | HTML + Word | HTML + Word |
| Visualisations | 4 (coup de cœur) | Illimitées | Illimitées |

La configuration exacte des plans vit dans `utils/plans_config.py` — c'est la **source unique de vérité**, ne la redéfinissez nulle part ailleurs.

---

## 🏗️ Architecture technique

| Composant | Technologie |
|---|---|
| Frontend & hébergement | Streamlit Community Cloud |
| Authentification & base de données | Supabase (Auth natif + Postgres + Edge Functions) |
| Paiements | Stripe (Checkout, Customer Portal, Webhooks) |
| Webhook relay | Supabase Edge Function (Deno/TypeScript) |
| Email transactionnel | Brevo (SMTP) |
| IA | Anthropic Claude API (exclusivement) |

**Flux résumé** : Streamlit ne peut pas recevoir de webhooks directement, donc les événements Stripe (renouvellement, échec de paiement, annulation) passent par une Edge Function Supabase qui met à jour la table `profiles`. L'app Streamlit lit ensuite simplement Supabase pour connaître le plan actif de l'utilisateur.

Pour le détail opérationnel (comment tout ça a été configuré, pièges connus, procédure manuelle pour l'Enterprise), voir `IMPLEMENTATION_GUIDE.md`.

## 📁 Structure du projet

```
ai-report-generator/
├── app.py                          # Application principale Streamlit
├── config.py                       # Configuration et traductions
├── requirements.txt
├── .streamlit/
│   └── config.toml                 # maxUploadSize, etc.
├── supabase/functions/stripe-webhook/
│   └── index.ts                    # Edge Function : sync Stripe → Supabase
│
├── utils/
│   ├── __init__.py
│   ├── auth_supabase.py            # Auth (Supabase Auth natif) + reset password
│   ├── plans_config.py             # ⭐ Source unique de vérité des plans
│   ├── stripe_checkout.py          # Checkout, Customer Portal, retour de paiement
│   ├── data_loader.py
│   ├── data_cleaner.py
│   ├── analyzer.py
│   ├── visualizations.py
│   ├── chart_curator.py            # Sélection IA des graphiques "coup de cœur"
│   ├── ai_insights.py              # Génération des insights (Anthropic + fallback basique)
│   ├── report_chat.py              # Chat conversationnel post-rapport
│   └── sample_data.py              # Dataset d'exemple généré à la volée
│
└── exports/
    ├── __init__.py
    ├── html_export.py              # Export HTML (imprimable en PDF)
    └── word_export.py              # Export Word
```

## 🚀 Installation locale (développement)

### Prérequis
- Python 3.9+
- Comptes : Supabase, Stripe, Anthropic, Brevo (voir `IMPLEMENTATION_GUIDE.md` pour la configuration complète de chacun)

### Étapes

```bash
git clone (https://github.com/Platini20/ai-report-generator.git)
cd ai-report-generator

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

Créez `.streamlit/secrets.toml` (jamais commité) avec :

```toml
SUPABASE_URL = "https://xxxxx.supabase.co"
SUPABASE_ANON_KEY = "..."
SUPABASE_SERVICE_KEY = "..."
STRIPE_SECRET_KEY = "sk_test_..."
STRIPE_PRICE_ID_PRO = "price_..."
APP_URL = "http://localhost:8501"

[anthropic]
api_key = "sk-ant-..."
```

```bash
streamlit run app.py
```

## 🌐 Déploiement (production)

Déployé sur **Streamlit Community Cloud**, connecté au dépôt GitHub `ai-report-generator` (branche `main`). Les secrets se configurent dans Streamlit Cloud → Settings → Secrets (même structure TOML que ci-dessus, avec `APP_URL` pointant vers l'URL publique de l'app).

La configuration Supabase, Stripe et Brevo (webhooks, templates email, SMTP) est détaillée dans `IMPLEMENTATION_GUIDE.md`.

## 🐛 Résolution de problèmes courants

| Problème | Solution |
|---|---|
| `ModuleNotFoundError` après ajout d'une dépendance | Vérifier `requirements.txt`, redéployer |
| Erreur `st.secrets has no key "X"` | Vérifier que la clé est bien **avant** toute section `[...]` dans les secrets (TOML) |
| Webhook Stripe en 401 | Le toggle "Enforce JWT Verification" de l'Edge Function s'est réactivé — le désactiver à nouveau après chaque déploiement |
| Upload refusé au-delà de 200 MB | Ajuster `maxUploadSize` dans `.streamlit/config.toml` |
| Erreur fichier Excel/Parquet | `pip install openpyxl` / `pip install pyarrow` |

## 👨‍💻 Auteur

**Franklin Agouanet**
- 💼 LinkedIn : [Franklin Platini Agouanet](https://www.linkedin.com/in/franklin-platini-agouanet-29a081156)
- 📧 Email : agouanetf@yahoo.com

## 📝 Licence

Projet propriétaire — tous droits réservés.
