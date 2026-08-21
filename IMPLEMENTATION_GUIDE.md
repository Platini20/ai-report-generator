# 🎯 Guide Technique & Opérationnel (interne)

Ce document remplace l'ancien guide d'implémentation (qui référençait des fichiers obsolètes : `subscription.py`, `app_commercial.py`, `auth_trial_updated.py`, un système à 4 plans avec Ollama). Il décrit l'architecture **actuelle**, comment elle a été construite, et les procédures opérationnelles pour Franklin (seul développeur).

---

## 🗺️ Vue d'ensemble du flux

```
Utilisateur (navigateur)
    │
    ▼
Streamlit Community Cloud (app.py)
    │
    ├──► Supabase Auth ──► inscription / connexion / reset mot de passe
    │         │
    │         ▼
    │    Table "profiles" (plan, quota, infos Stripe) ──RLS──► lecture/écriture via clé service_role
    │
    ├──► Anthropic API ──► génération des insights + chat conversationnel + sélection des graphiques
    │
    └──► Stripe Checkout ──► paiement Pro
              │
              ▼
         Stripe Webhook ──► Supabase Edge Function (stripe-webhook)
                                  │
                                  ▼
                          Met à jour "profiles" (renouvellement, échec paiement, annulation)
```

**Pourquoi une Edge Function ?** Streamlit ne peut pas recevoir de requêtes HTTP entrantes (webhooks) — ce n'est pas un serveur classique. La Edge Function Supabase sert de relais : Stripe l'appelle, elle met à jour Supabase, et l'app Streamlit se contente de lire Supabase au moment de la connexion de l'utilisateur.

---

## 📦 Source unique de vérité : `plans_config.py`

Toute la configuration des 3 plans (Trial, Pro, Enterprise) vit dans `utils/plans_config.py` : quotas, tailles de fichiers, formats d'export, nombre de visualisations. **Ne jamais redéfinir un plan ailleurs** — c'est exactement le problème qui existait avant (deux fichiers avec des chiffres différents et désynchronisés).

Le Price ID Stripe (`price_...`) n'est volontairement PAS dans ce fichier — il vit dans `st.secrets["STRIPE_PRICE_ID_PRO"]` pour éviter de committer des identifiants dans Git.

---

## 🔐 Authentification (Supabase Auth natif)

- Les mots de passe sont gérés entièrement par Supabase (jamais de hash maison).
- Un trigger SQL (`handle_new_user`, voir `database_schema.sql`) crée automatiquement une ligne `profiles` à chaque inscription.
- **Reset de mot de passe** : utilise le flux `token_hash` (pas `access_token` en fragment d'URL, illisible côté serveur Streamlit). Le template email "Reset Password" dans Supabase doit contenir :
  ```
  {{ .SiteURL }}/?type=recovery&token_hash={{ .TokenHash }}
  ```
- **Piège connu** : la personnalisation des templates email et le volume d'envoi (2/heure par défaut) nécessitent un SMTP externe. On utilise **Brevo** (300 emails/jour gratuit, pas besoin de domaine vérifié — juste une adresse email individuelle validée).

---

## 💳 Paiements (Stripe)

### Checkout
`utils/stripe_checkout.py` crée une session Stripe Checkout et gère le retour (`?checkout=success&session_id=...`) : à ce moment, l'app vérifie le paiement auprès de Stripe et met à jour Supabase immédiatement — c'est un flux **synchrone**, complémentaire au webhook (qui couvre les événements asynchrones : renouvellement, échec, annulation).

### Customer Portal
Bouton "Gérer mon abonnement" pour les utilisateurs Pro — ouvre le portail Stripe (annulation, moyen de paiement, factures), zéro code de gestion à maintenir côté app.

⚠️ En mode test, le Customer Portal doit être activé une fois dans Stripe Dashboard → Billing → Customer portal → "Activate test link".

### Webhook (Edge Function `stripe-webhook`)
Événements gérés : `invoice.paid` (reset quota mensuel), `invoice.payment_failed` (statut `past_due`), `customer.subscription.deleted` (retour au plan Trial), `customer.subscription.updated` (sync statut).

⚠️ **Piège récurrent** : le toggle "Enforce JWT Verification" de l'Edge Function se **réactive automatiquement à chaque déploiement**. Si Stripe reçoit des 401, c'est toujours la première chose à vérifier (Edge Functions → stripe-webhook → Details → Security).

---

## 🎯 Gestion manuelle du plan Enterprise

Aucune automatisation pour l'instant (volume faible attendu au lancement) :

1. Négociation par email (`agouanetf@yahoo.com`, via le lien "Contact us" replié dans l'app)
2. Supabase → Table Editor → `profiles` → trouver le compte par email → `plan = enterprise`, `reports_limit = -1`, `subscription_status = active`
3. (Optionnel) Créer un abonnement à prix personnalisé dans Stripe Dashboard (mode live), copier le `stripe_customer_id` généré vers Supabase pour que le client puisse utiliser le Customer Portal

Si le volume augmente, envisager une petite page admin dans l'app plutôt que cette procédure manuelle.

---

## 🖨️ Export PDF

Pas de module de génération PDF dédié — le PDF est obtenu en imprimant le rapport HTML (le CSS `@media print` de `html_export.py` gère déjà une mise en page imprimable propre). C'est pourquoi "PDF" n'apparaît pas comme format de téléchargement séparé dans l'app, seulement comme instruction ("téléchargez le HTML, Ctrl+P, Enregistrer en PDF").

---

## 🧠 Insights IA

- Modèle utilisé : `claude-sonnet-4-5-20250929` (voir `ai_insights.py`, `report_chat.py`, `chart_curator.py`)
- **Mode basique** (sans IA) sert de filet de sécurité si l'API Anthropic échoue — ne décompte **pas** le quota de rapports dans ce cas (transparence envers l'utilisateur)
- **Chat conversationnel** : répond à partir des statistiques déjà calculées, jamais des lignes brutes du fichier. Limité à 30 messages par rapport (protection anti-abus, pas lié au quota payant)
- **Graphiques "coup de cœur"** : sélection IA des 4 visualisations les plus pertinentes (appel texte léger, jamais d'image envoyée à l'API). Repli automatique sur un ordre de priorité par défaut si l'API échoue

---

## 🔒 Confidentialité — résumé technique

- Fichiers uploadés : en mémoire (`st.session_state`) uniquement, jamais persistés
- Anthropic reçoit des statistiques agrégées (noms de colonnes, moyennes, etc.), jamais les lignes brutes
- Mots de passe : gérés par Supabase Auth, jamais vus par le code de l'app
- Paiements : gérés par Stripe, l'app ne stocke qu'un `stripe_customer_id`

---

## 🚧 Limites connues / dette technique

- `analyzer.py` limite l'analyse catégorielle aux 10 premières colonnes du fichier (au-delà, non analysées) — acceptable pour l'instant, à revoir si des clients uploadent des fichiers très larges
- Le plan affiché dans l'app ne se resynchronise qu'à la **connexion** — un changement de plan en cours de session (ex: annulation via Stripe pendant que l'utilisateur est connecté) ne se reflète qu'après reconnexion
- Pas de page admin — toute intervention (Enterprise, correction manuelle) se fait directement dans Supabase
- Export PowerPoint non implémenté (mentionné nulle part dans l'UI actuellement, correctement retiré de `export_formats`)

## 📋 Roadmap restante

- **Lien de rapport partageable publiquement** (différenciation produit, pas encore fait)
- Page admin si le volume Enterprise augmente
- Réactiver la confirmation email Supabase avant un vrai lancement public (désactivée pendant les tests)
- Régénérer les clés Anthropic/Supabase/Stripe si elles ont été partagées en clair pendant le développement (rappel sécurité)
