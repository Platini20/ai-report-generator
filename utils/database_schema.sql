-- ==========================================================
-- SCHÉMA SUPABASE — Générateur de Rapports IA (version payante)
-- À exécuter dans : Supabase Dashboard → SQL Editor → New query
-- ==========================================================

-- ------------------------------------------------------------
-- 1) TABLE PROFILES
-- Note : Supabase Auth gère déjà "auth.users" (email, mot de passe,
-- confirmation email, etc.). Cette table stocke UNIQUEMENT les
-- infos métier : plan, quota, Stripe.
-- ------------------------------------------------------------
create table public.profiles (
    id                       uuid references auth.users(id) on delete cascade primary key,
    email                    text not null,
    plan                     text not null default 'trial'
                                 check (plan in ('trial', 'pro', 'enterprise')),
    reports_used             integer not null default 0,
    reports_limit            integer not null default 3,
    reports_reset_at         date,                      -- prochaine date de remise à zéro (plans payants, mensuel)
    stripe_customer_id       text,
    stripe_subscription_id   text,
    subscription_status      text default 'none',       -- none | active | past_due | canceled
    created_at               timestamptz not null default now(),
    updated_at               timestamptz not null default now()
);

-- ------------------------------------------------------------
-- 2) SÉCURITÉ (RLS)
-- L'app Streamlit lit/écrit via la clé service_role (contexte serveur
-- de confiance, jamais exposée au navigateur), donc elle bypass RLS.
-- Ces règles protègent la table si un accès direct est ajouté plus tard
-- (ex: futur frontend qui interroge Supabase depuis le navigateur).
-- ------------------------------------------------------------
alter table public.profiles enable row level security;

create policy "Un utilisateur peut lire son propre profil"
    on public.profiles for select
    using (auth.uid() = id);

-- Pas de policy UPDATE pour les utilisateurs : seule la clé service_role
-- (utilisée par l'app) peut modifier plan/quota/Stripe. Évite qu'un
-- utilisateur ne s'auto-passe en plan "enterprise" via l'API publique.

-- ------------------------------------------------------------
-- 3) TRIGGER : création automatique du profil à l'inscription
-- Dès qu'un utilisateur s'inscrit via Supabase Auth (auth.users),
-- une ligne "profiles" est créée automatiquement en plan trial.
-- ------------------------------------------------------------
create or replace function public.handle_new_user()
returns trigger as $$
begin
    insert into public.profiles (id, email, plan, reports_used, reports_limit)
    values (new.id, new.email, 'trial', 0, 3);
    return new;
end;
$$ language plpgsql security definer;

create trigger on_auth_user_created
    after insert on auth.users
    for each row execute procedure public.handle_new_user();

-- ------------------------------------------------------------
-- 4) TABLE PAYMENTS_LOG (préparée pour la Phase 3 — webhook Stripe)
-- Historique brut de chaque événement Stripe reçu, utile pour le
-- support et le débogage. Accessible uniquement via service_role.
-- ------------------------------------------------------------
create table public.payments_log (
    id               uuid primary key default gen_random_uuid(),
    user_id          uuid references auth.users(id) on delete set null,
    stripe_event_id  text unique,
    event_type       text,
    raw_payload      jsonb,
    created_at       timestamptz not null default now()
);

alter table public.payments_log enable row level security;
-- Aucune policy publique = accessible uniquement via la clé service_role.

-- ------------------------------------------------------------
-- 6) TABLE ANONYMOUS_TRIALS — suivi du quota d'essai SANS compte
-- Identifié par un device_id stocké côté navigateur (localStorage).
-- Accessible uniquement via la clé service_role (comme payments_log).
-- ⚠️ Contournable en vidant le cache navigateur — compromis assumé
-- pour réduire la friction d'essai (voir IMPLEMENTATION_GUIDE.md).
-- ------------------------------------------------------------
create table public.anonymous_trials (
    device_id      text primary key,
    reports_used   integer not null default 0,
    reports_limit  integer not null default 3,
    created_at     timestamptz not null default now(),
    updated_at     timestamptz not null default now()
);

alter table public.anonymous_trials enable row level security;
-- Aucune policy publique = accessible uniquement via service_role.

-- ------------------------------------------------------------
-- 7) INDEX utiles
-- ------------------------------------------------------------
create index idx_profiles_email on public.profiles(email);
create index idx_profiles_stripe_customer on public.profiles(stripe_customer_id);
