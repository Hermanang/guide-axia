# Onboarding dev & CI — AXIA ISP (1 page)

> Cible : un nouveau développeur obtient une instance Odoo 18 LTS fonctionnelle via
> `docker compose up` en **< 15 minutes**, et comprend la pipeline CI qui valide chaque PR.

## 1. Pré-requis poste

- Docker ≥ 24 + Docker Compose v2 (`docker compose version`)
- Git, Python 3.11+ (pour `pre-commit` en local), ~4 Go RAM libres
- Ports libres : `8069` (Odoo), `5432` (Postgres), `6379` (Redis), `9090` (Prometheus)

## 2. Démarrage local

L'infra Docker/Odoo est regroupée dans **`deploy/`** ; on démarre depuis ce dossier.

```bash
git clone <repo-url> && cd splynx-odoo/deploy
cp .env.example .env          # renseigner les placeholders avec des valeurs de dev
docker compose up             # build (Odoo 18 + deps + OCA vendorés) puis lance la stack
```

- `odoo-init` (one-shot) crée et initialise la base **`axia_dev`** (base + `queue_job`) au 1er boot.
- Odoo : http://localhost:8069 (base `axia_dev`, conforme à `db_filter` = `^axia.*$`).
- Le worker `queue_job` (`odoo-jobrunner`) tourne dans un **process séparé** du web (NFR-12),
  `--load=base,web,queue_job` → jobrunner OCA actif, channels `odoo.conf` (ADR-009).
- Arrêt : `docker compose down` (ajouter `-v` pour repartir d'une base vierge).
- Prod (sans surcharge dev) : `docker compose -f docker-compose.yml up`.

### Dépannage rapide

| Symptôme | Cause probable | Action |
|---|---|---|
| `odoo-init` en échec | Postgres pas prêt / addons manquants | `docker compose logs odoo-init` |
| Odoo `unhealthy` au boot | init pas terminé | attendre `odoo-init` (service_completed_successfully) |
| Port 8069 occupé | autre instance Odoo | `docker compose down` ou changer le mapping dans l'override |
| Jobs jamais exécutés | jobrunner down | `docker compose logs odoo-jobrunner` |

## 3. Qualité locale (avant push)

```bash
pip install pre-commit && pre-commit install
pre-commit run --all-files    # black, isort, pylint-odoo
```

## 4. Pipeline CI (GitHub Actions)

Déclenchée sur **chaque `pull_request`** (`.github/workflows/ci.yml`). Étapes, toutes
**bloquantes** (un échec ⇒ PR rouge) :

1. **`pre-commit`** — `black`, `isort`, `pylint-odoo` sur tout le repo.
2. **Tests par module en parallèle** — stratégie `matrix` (un job par module `axia_*`,
   `axia_audit` initialement), runner `pytest` + `pytest-odoo`, isolation via `--test-tags`.
3. **Détection de secrets** — scan des sources/logs (`detect-secrets` / grep) : aucune
   fuite de mot de passe, token ou clé.
4. **Référence pen test cross-company** — invoque `scripts/pen_test_cross_company.py`
   (script réel livré en Story 0.3 ; la step est tolérante tant qu'il est absent).

> Hors scope Story 0.1 (différés) : workflow `release.yml` (build/push image sur tag)
> et premier tag `vX.Y.Z`. Les classes ATDD `TestReleasePipeline` /
> `TestFirstReleaseTagDemonstratesPath` restent volontairement rouges.

## 5. Structure du repo

```
deploy/              infra Docker/Odoo : compose(.override), Dockerfile, odoo.conf,
                     requirements.txt, .env.example, prometheus.yml, axia-entrypoint.sh
addons/              modules métier axia_* (axia_audit en Story 0.4)
third_party_addons/  vendoring OCA : queue_job + connector(+component/_event) @18.0
                     (pins dans OCA_PINS.txt ; keychain non porté en 18.0, cf. README)
scripts/             scripts d'appoint (pen test, init SQL…)
docs/adr/            ADR additionnels (les 10 canoniques sont dans architecture.md)
.github/workflows/   pipelines GitHub Actions (figé racine — GitHub n'exécute que ça)
```
