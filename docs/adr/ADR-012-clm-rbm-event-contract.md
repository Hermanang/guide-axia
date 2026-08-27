# ADR-012 — Contrat événementiel CLM ↔ RBM

- **Status: Accepted** (livré Story 5.1 sprint amorce commun CLM+RBM)
- Date : 2026-08-11
- Portée : Epic 5 (CLM — Customer Lifecycle Management) + Epic 6 (RBM — Recurring Billing Management)
- Story source : 5.1 (sprint amorce commun, jumelée avec 6.1)
- Modules concernés : `axia_clm` (NEW), `axia_rbm` (NEW), `axia_audit` (extension `event_types.csv`)
- Errata numérotation : `sprint-change-proposal-2026-08-10-clm-rbm.md` §4.1 mentionne « ADR-011 ». Le numéro 011 est déjà pris par `axia_credential_generator` (Story 0.5). Le nouveau ADR reçoit **ADR-012** conformément au principe d'immutabilité des numéros ADR (Nygard 2011).

## Contexte

Le PRD CLM+RBM (`_bmad-output/planning-artifacts/spec-clm-rbm/prd-axia-clm-rbm.md`) §6 impose une séparation stricte entre le module de gestion du cycle de vie contractuel (CLM) et le module de facturation récurrente (RBM). Les deux modules communiquent **exclusivement par événements identifiés** — jamais par appel direct, jamais par import Python cross-module, jamais par accès ORM au modèle de l'autre.

Le contrat événementiel doit être **figé formellement dans le code** dès le sprint amorce commun (Story 5.1 = Story 6.1 jumelée) pour que les 2 chantiers puissent démarrer en parallèle sans dérive.

## Décisions

### D1 — Transport asynchrone `queue_job` OCA

Bus événementiel asynchrone via `queue_job` OCA (cohérent ADR-009). Rejet des alternatives :

- **`odoo.event` / signaux natifs** — synchrone, couple les deux modules à l'exécution, casse le principe cardinal « CLM décide, RBM exécute ».
- **Table dédiée + cron batch pull** — latence 15 min inacceptable pour `suspension_required` / `reactivation_required` (SLA 5 min p95, NFR-3 / NFR-4).
- **Appels de service directs Python (import cross-module)** — couple fort, cassure du contrat, empêche évolution indépendante.

Extension channels ADR-009 (à créer au 1er émission réelle, hors périmètre 5.1) :

```
root.clm_rbm.orders:2         # ordres CLM→RBM (create/policy/close)
root.clm_rbm.events:2         # events RBM→CLM (issued/paid/received)
root.clm_rbm.critical:5       # suspension_required / reactivation_required (SLA 5 min p95)
root.clm_rbm.audit:1          # events audit internes §6.5
```

### D2 — Format payload JSON Schema Draft-07

**JSON Schema Draft-07** (pas Draft-2020-12) — motif : `jsonschema.Draft7Validator` est stable, transitif via OCA `queue_job`, largement supporté. Draft-2020-12 ajoute `unevaluatedProperties` mais est overkill pour 17 schémas plats sans composition profonde.

Chaque événement de frontière (§6.2 + §6.3) porte un schéma JSON figé livré :

- `addons/axia_clm/data/event_schemas/*.json` × 9 (8 ordres §6.3 + `credit_note_order` correctif C1).
- `addons/axia_rbm/data/event_schemas/*.json` × 9 (§6.2, incluant `credit_note_issued` + `closure_completed` explicités par correctif C1).

Chaque schéma déclare `"$schema": "http://json-schema.org/draft-07/schema#"`, `"type": "object"`, `"required"` listant le payload minimum §6.2/§6.3, `"additionalProperties": false` (garde strict).

### D3 — Registry Python `axia_clm.services.registry`

Le registry est livré dans `axia_clm/services/registry.py` (pas dans `axia_audit`) — motif : la fixture ATDD `event_schema_registry` (`_bmad-output/test-artifacts/atdd-shared/conftest_clm_rbm.py` L253-263) impose l'emplacement `from odoo.addons.axia_clm.services import registry`. Alternative « registry dans axia_audit » rejetée : imposerait de retoucher le conftest ATDD déjà scellé et coupler `axia_audit` (foundation) à la nomenclature CLM+RBM.

Le registry importe les schémas des 2 modules via `importlib.resources` (chemins fichiers uniquement, aucun import Python cross-module) :

- `get_schema(event_type: str) -> dict | None` — retourne le JSON Schema chargé.
- `emit(event_type: str, payload: dict, correlation_id: str) -> None` — valide le payload contre `get_schema(event_type)` ; sur échec lève `AxiaEventSchemaViolation` (sous-classe de `odoo.exceptions.ValidationError`) **avant** tout `queue_job.delay`.

### D4 — `correlation_id` propagé bout-en-bout

`correlation_id` (UUID v4) présent dans le payload JSON ET dans les headers `queue_job` (compat ADR-010). Généré au point d'entrée (UI, cron, webhook Splynx) — aucun événement downstream ne le régénère.

### D5 — Idempotence via `event_id`

Chaque événement porte `event_id` UNIQUE (UUID v4). Déduplication via nouveau modèle `axia.event.inbox` (miroir `axia.webhook.inbox`, UNIQUE INDEX sur `(event_type, event_id)`, purge fenêtre 24 h).

**Différé au 1er vrai emit** (Story 5.6 CLM→RBM ordres / Story 6.2 RBM→CLM events) — Story 5.1 se limite au contrat + validation format. L'infrastructure de bus (envelope + inbox + channels queue_job) suit dans les stories fonctionnelles.

### D6 — Correctif C1 (readiness report 2026-08-10) — 5 événements ambigus explicités

Le readiness report (`_bmad-output/planning-artifacts/implementation-readiness-report-2026-08-10-clm-rbm.md` §C1) identifie 5 événements dont l'émetteur ou la portée n'étaient pas clairs. Décisions figées ici :

| Événement | Direction | Émetteur | Décision | Motif |
|---|---|---|---|---|
| `credit_note_issued` | RBM→CLM | Story 6.9 (émission avoir) | **Déclaré** — `module_owner=axia_rbm`, schéma livré `axia_rbm/data/event_schemas/credit_note_issued.json` | §6.2 PRD explicite : le RBM notifie le CLM à chaque avoir (que la source soit `clm_order` ou `manual_accounting`). |
| `closure_completed` | RBM→CLM | Story 6.13 (retour de `billing_account_close`) | **Déclaré** — `module_owner=axia_rbm`, schéma livré `axia_rbm/data/event_schemas/closure_completed.json` | §6.2 PRD explicite : le RBM confirme au CLM la fin de la liquidation financière. |
| `credit_note_order` | CLM→RBM | CLM (geste commercial) | **Déclaré** — `module_owner=axia_clm`, schéma livré `axia_clm/data/event_schemas/credit_note_order.json` + stub `_emit_credit_note_order` sur `axia.contract` | §6.3 PRD explicite : le CLM peut ordonner un avoir (correction de pénalité, ajustement contractuel). |
| `refund_processed` | (candidat) | (indéfini) | **RETIRÉ** — non déclaré dans `event_types.csv`, pas de schéma livré | Redondant avec `deposit_refunded` (§6.2 PRD) + `payment_received` (§6.2 PRD). Aucune sémantique orthogonale. Le brouillon du correctif C1 mentionnait un candidat sans motif fonctionnel — pas de trace §6.2/§6.3. |
| `audit_rbm_internal` | (candidat) | (indéfini) | **RETIRÉ** — non déclaré dans `event_types.csv`, pas de schéma livré | Hors §6.5 audit interne = pas un événement de frontière. Le catalogue §6.5 liste 11 événements audit orthogonaux nommés en `<domaine>.<action>[.<qualificatif>]` (dot-separated) ; il n'y a pas de « super-audit » agrégé nommé `audit_rbm_internal`. Le brouillon C1 confondait la couche frontière et la couche audit interne. |

Les 2 événements retirés (`refund_processed` + `audit_rbm_internal`) restent traçables ici pour l'histoire ; toute réintroduction future exigera un nouvel ADR (ou un amendement daté) documentant la sémantique nouvelle et distincte.

### D7 — Contradiction G2 résolue — 17 frontière + 11 audit interne = 28 événements totaux

Le PRD CLM+RBM §1.4 parle de « 9 sortants RBM + 8 entrants CLM = 17 » ; §6.5 mentionne 11 événements d'audit interne. La contradiction apparente vient d'une confusion de couche : ce sont deux couches orthogonales.

**Matrice normative** (mise à jour post-correctif C1 — Story 5.1 review, décision produit 2026-08-11) :

| Couche | Nombre | Source PRD | Convention naming | Colonne `payload_schema` CSV | Franchit la frontière CLM/RBM ? |
|---|---|---|---|---|---|
| Frontière RBM → CLM | 9 (incl. C1 : `credit_note_issued`, `closure_completed`) | §6.2 | `<domain>_<action>` (underscore) | Chemin `axia_rbm/data/event_schemas/<event>.json` | Oui |
| Frontière CLM → RBM | 9 (incl. C1 : `credit_note_order`) | §6.3 | `<domain>_<action>` (underscore) | Chemin `axia_clm/data/event_schemas/<event>.json` | Oui |
| Audit interne | 11 | §6.5 | `<domain>.<action>[.<qualifier>]` (dot) | Marker `actor+target+delta` | Non (produits ET consommés dans un même module ou par le connecteur Splynx) |
| **Total événements déclarés `axia_audit/data/event_types.csv`** | **29** | | | | |

**Contrat de nomenclature figé** :

- **Underscore = frontière contractuelle** — engagement inter-module, versionné (bump `v1 → v2` requiert nouveau schéma + adaptateur consommateur).
- **Dot = audit interne** — journal d'exécution, évolution libre au sein du module propriétaire.

Aucun événement d'audit interne ne doit être utilisé comme substitut à un événement de frontière (§6.5 PRD dernière ligne).

**Convention colonne `payload_schema` de `event_types.csv`** (Story 5.1 review, décision code-review CR9(a) 2026-08-11) — le champ `axia.audit.event.type.payload_schema` (Char, help "indicatif") porte deux formats coexistants :

- **Ends with `.json`** → chemin relatif vers un JSON Schema Draft-07 chargé par `axia_clm.services.registry` via `importlib.resources`. Le registry est la source de vérité pour la validation ; la colonne CSV est **indicative** (un consommateur qui veut valider un payload frontière doit passer par `registry.get_schema(event_type)`, pas parser le path CSV).
- **Sinon (typiquement `actor+target+delta`)** → marker sémantique convention `axia.audited.mixin._audit()` (audit interne, pas de validation JSON Schema).

Cette overload est **assumée** et **codifiée** : elle évite d'ajouter une colonne discriminante `schema_kind` (bump modèle Odoo + migration). Un consommateur de la colonne doit case-splitter `if ps.endswith(".json"): use_registry else: ...`. La règle est stable ; toute évolution nécessiterait une migration + un bump d'`axia.audit.event.type`.

### D8 — Interdictions strictes (fail-CI)

- **Aucun** `from odoo.addons.axia_rbm import ...` dans `axia_clm/*` (et symétrique).
- **Aucun** `self.env['axia.contract']` dans `axia_rbm/*` (et symétrique sur `axia.billing.account` depuis `axia_clm`).
- **Aucun** `self.env['res.partner'].create(...)` avec effet CLM ou RBM en dehors des modules propriétaires.

**Enforcement Story 5.1** : script grep `scripts/check_no_cross_module_import.sh` au workflow CI, exit 1 si import cross-module détecté. Extension pylint custom rule différable à Story 4.4 (correlation_id CI garde).

#### D8.1 — Exceptions whitelistées (amendement Story 6.2 code review, décision Kelvin 2026-08-23)

Deux imports cross-module `axia_clm → axia_rbm` sont **explicitement autorisés** parce que ce sont des modules Python **purs** (aucun `models.Model`, aucun `self.env`, aucun accès ORM) :

1. **`from odoo.addons.axia_clm.services import registry`** — module ADR-012 §D3, source unique de validation JSON Schema Draft-07 pour tous les events frontière. Le handler `axia.rbm.handler.on_billing_account_create` (Story 6.2 AC6) l'appelle pour la défense en profondeur du payload (`registry.validate("billing_account_create", payload)`). Dupliquer la logique de validation côté `axia_rbm` violerait DRY et créerait une deuxième source de vérité qui peut dériver de la première au fil des bumps du schéma.

2. **`from odoo.addons.axia_clm.exceptions import ...`** — module Python d'exceptions pures (aujourd'hui `AxiaEventSchemaViolation`, sous-classe `ValidationError`). Le handler doit pouvoir lever/catcher les types métier communs (chain forensic partagée), les tests RBM doivent pouvoir `assertRaises(AxiaEventSchemaViolation)`.

**Enforcement** : `scripts/check_no_cross_module_import.sh` whitelist ces 2 imports en post-filter `grep -vE`. Toute autre forme (imports `from odoo.addons.axia_clm.models`, `from odoo.addons.axia_clm.utils`, etc.) reste bloquée fail-CI.

**Invariants à préserver** :
- `axia_clm/services/registry.py` NE DOIT PAS importer de `models.Model` ni faire d'accès `env.cr` — c'est un module fonctionnel pur (audit à chaque story qui touche le fichier).
- `axia_clm/exceptions.py` NE DOIT contenir QUE des sous-classes d'`Exception` — pas de logique métier, pas d'import de modèles ORM.

Si un de ces 2 invariants doit être violé (justification forte : cache LRU nécessitant `env`, exception ORM native, etc.), amender ADR-012 §D8.1 avant merge et re-évaluer la whitelist CI.

### D9 — Compatibilité ADR existants

- **ADR-005** (audit schéma) : réutilise `axia_audit_event` pour tracer les events. Étend `event_types.csv` par 28 nouvelles entrées (17 frontière + 11 audit interne).
- **ADR-009** (queue_job channels) : extension par 4 channels `root.clm_rbm.*` (à créer au 1er emit — Story 5.6 / 6.2).
- **ADR-010** (correlation_id) : réutilise `axia.correlation` (dans `axia_audit`) — aucune duplication.
- **ADR-005 partitionnement** : les nouveaux événements CLM+RBM alimentent la même table partitionnée mensuelle — pas de nouvelle partition dédiée.

### D10 — Interaction `axia_billing_workflow` (Story 3.13 adapter RBM)

Le sous-module `axia_billing_workflow.rbm_adapter/` (Story 3.13, hors périmètre 5.1) traduit les events internes du workflow d'impayés vers RBM :

- `invoice.overdue.detected` → `invoice_overdue`
- `suspension.scheduled` → `suspension_required`
- `suspension.executed` → (audit interne uniquement)
- `account.payment.received` → `payment_received`
- `reactivation.executed` → `reactivation_required`

Paramètre tenant `suspension_approval_mode ∈ {automatic, manual, hybrid}` (dans `axia_admin_params`, extension §CLM-BD-05 architecture). Défaut `automatic` = comportement workflow actuel préservé.

### D11 — Discipline « 1er consommateur » étendue aux dépendances de manifest (Kelvin 2026-08-11)

Cette décision étend au périmètre « dépendances » le principe déjà tranché pour RBAC via `decision-rbac-roles-lean-policy-vs-mecanisme` : on déclare la dépendance au 1er consommateur réel, pas par anticipation.

**Application Story 5.1** : `axia_billing_workflow` et `axia_admin_params` sont RETIRÉS temporairement de `axia_rbm.__manifest__.py::depends`. Motif : ces 2 modules n'existent pas encore dans `addons/` (Epic 3 backlog), et aucun code livré en 5.1 ne les consomme (scaffold + stubs uniquement, pas d'ImportError). Manifest livré :

```python
"depends": ["base", "axia_audit", "axia_rbac", "axia_splynx_connector"],
# TODO Story 3.13 : ajouter `axia_billing_workflow` au 1er consommateur réel.
# TODO Story 6.11 : ajouter `axia_admin_params` au 1er consommateur réel.
```

Dettes tracées dans `deferred-work.md` :

- **`5.1-DEF1`** — Réintégrer `axia_billing_workflow` au démarrage Story 3.13 (adapter RBM sur workflow d'impayés).
- **`5.1-DEF2`** — Réintégrer `axia_admin_params` au démarrage Story 6.11 (politique dunning configurable 6 paliers).

Horizon Epic 3 = cette semaine ou la suivante → dettes courtes.

Alternatives rejetées :

- **Option A** (scaffold 2 modules vides `axia_billing_workflow` + `axia_admin_params` maintenant) — anti-sur-ingénierie, périmètre 5.1 dépassé.
- **Option C** (bloquer 5.1 sur Epic 3) — casse le mandat SCP 2026-08-10 « sprint amorce commun démarre en parallèle chantier 3 ».

## Acceptation (vérifiable)

- 100 % des 17 événements de frontière ont un schéma JSON Draft-07 livré et validable par `axia_clm.services.registry.get_schema()`.
- Le snapshot `_bmad-output/test-artifacts/golden-files/event_schemas_v1_hashes.json` fige les 18 hashes sha256 canoniques ; toute divergence non-approuvée par bump `v1 → v2` échoue la CI (test `test_event_contract_stability`).
- `axia_clm` et `axia_rbm` s'installent tous les deux sans erreur sur une base fraîche.
- Grep manifests : aucune dépendance Enterprise (`sale_subscription`, `sign`, `documents`, `helpdesk`) déclarée.
- Grep cross-module : aucun `from odoo.addons.axia_rbm` dans `axia_clm/`, aucun `from odoo.addons.axia_clm` dans `axia_rbm/`, aucun accès ORM cross (`axia.contract` depuis `axia_rbm`, `axia.billing.account` depuis `axia_clm`).
- `correlation_id` constant sur chaîne complète *UI action → CLM → queue_job → RBM → workflow → Splynx → audit* — vérification à Story 4.4 DoD étendu (chaînes E2E chantier 4).
- Latence ordres critiques ≤ 5 min p95 — exporter Prometheus `axia_clm_rbm_event_latency_seconds{event_type, direction}` alimenté par `envelope.processed_at − envelope.created_at` (à livrer au 1er vrai emit, Story 5.6 / 6.2).
- Idempotence : rejeu 100 events dupliqués → 0 side-effect — test intégration `tests/integration/test_event_idempotency.py` dans `axia_audit` (à livrer à la création de `axia.event.inbox`, Story 5.6 / 6.2).

## Références

- [PRD CLM+RBM §6](../../_bmad-output/planning-artifacts/spec-clm-rbm/prd-axia-clm-rbm.md#6-interface-clm--rbm) — source normative du contrat événementiel.
- [Architecture ADR-012 (extension 2026-08-10)](../../_bmad-output/planning-artifacts/architecture.md#adr-012--contrat-événementiel-clm--rbm) — synthèse historique.
- [Readiness report — correctif C1](../../_bmad-output/planning-artifacts/implementation-readiness-report-2026-08-10-clm-rbm.md) — mandat des 5 événements ambigus.
- [ADR-005](./) (audit schéma) — pattern `axia_audit_event` réutilisé.
- [ADR-009](./) (queue_job channels) — pattern étendu par 4 channels `root.clm_rbm.*`.
- [ADR-010](./) (correlation_id) — pattern `axia.correlation` réutilisé.
- [ADR-011](./) (`axia_credential_generator` Story 0.5) — précédent d'ADR fondation transverse.
