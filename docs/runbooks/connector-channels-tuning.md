# Runbook — Ajustement des channels queue_job du connecteur (post-POC R3)

Story 1.4. Concerne la concurrence des jobs de synchronisation Splynx.

## Topologie par défaut (ADR-009)

La concurrence runtime est déclarée dans [`deploy/odoo.conf`](../../deploy/odoo.conf)
section `[queue_job]` :

```
channels = root:1, \
           root.sync.xiwo:1, root.sync.weelax:1, \
           root.sync.coqla:1, root.sync.globalgrid:1, \
           root.webhook:5, root.reconcile:1, root.legacy_import:1
```

- **`root.sync.<marque>:1`** — un job de sync par marque à la fois (anti rate-limit
  Splynx ; fairness inter-marques, NFR-9). Le token `<marque>` = `backend.slug`
  (dérivé dans `axia.backend.splynx._sync_channel()`).
- Les enregistrements `queue.job.channel` correspondants sont matérialisés par
  [`data/queue_job_channels.xml`](../../addons/axia_splynx_connector/data/queue_job_channels.xml)
  (visibilité/déterminisme de test) — **ils ne portent PAS la concurrence**, qui
  vient exclusivement d'`odoo.conf`.

## Ajuster après le POC R3 (montée en charge réelle)

1. **Mesurer** : latence p95 éligibilité→`external_id` (cible ≤ 5 min, NFR-2) et le
   taux de 429 Splynx par marque (logs `splynx.request`).
2. **Si une marque sature** (volume de créations élevé sans 429) : augmenter sa
   capacité, p.ex. `root.sync.xiwo:2`. ⚠ Vérifier d'abord la tolérance de l'API
   Splynx de ce tenant — la concurrence 1 est volontairement conservatrice.
3. **Si Splynx renvoie des 429** : garder `:1` (voire réduire la cadence du cron) ;
   le client retry déjà en interne (1s/2s/4s) puis `RetryableJobError`.
4. **Nouvelle marque** : ajouter `root.sync.<slug>:1` dans `odoo.conf` ET un
   enregistrement enfant dans `queue_job_channels.xml`. Un slug absent des channels
   retombe sur `root` (concurrence partagée) — à éviter.
5. **Appliquer** : la modif `odoo.conf` exige un **redémarrage** du service
   `odoo-jobrunner` (process séparé, NFR-12) ; aucune migration de base.

## Channels hors périmètre 1.4

`critical/payment/suspend/reactivat` (workflow impayés) relèvent de l'**Epic 3** ;
leur naming/priorité ne sont pas tranchés ici (cf. test `test_e1_s22` skippé).
