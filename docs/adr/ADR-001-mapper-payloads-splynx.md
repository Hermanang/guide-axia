# ADR-001 — Contrat MapperV1 & payloads Splynx (POC golden files)

- **Status: Accepted** (D8 **révisé** 2026-06-22 ; D4 **confirmed live** 2026-06-23)
- **Statut : Accepté** (D8 révisé suite au 1er test réel contre un Splynx live ; D4 contrat écriture service confirmé live)
- Date : 2026-06-20 (révision D8 : 2026-06-22 ; confirmation D4 : 2026-06-23)
- Portée : Epic 1 (synchronisation Odoo ↔ Splynx), capacité MapperV1
- Story source : 0.2 — POC payloads Splynx, golden files sur 4 backends
- Golden files de référence : `addons/axia_splynx_connector/tests/golden/`

## Contexte

MapperV1 (Chantier 1) doit traduire les objets Odoo en payloads Splynx et lire le
monitoring Splynx. Pour éviter de coder sur des hypothèses documentaires, on a
capturé les **payloads réels** via l'API Splynx v2.0 (auth signature `Splynx-EA`,
HMAC-SHA256 de `nonce+key`) sur le **seul tenant `xiwo`** (lecture). Le contrat
des 3 autres tenants (`weelax`, `coqla`, `globalgrid`) n'est **pas recapturé** : il
est **inféré par uniformité de version** (D6, confirmée par le PO). Le monitoring
est complété par le **schéma officiel** de l'endpoint (liste live vide). Les 5
opérations cibles : `post_customer`, `post_internet_service`, `put_customer`,
`put_internet_service`, `monitoring`.

## Méthode de capture

- Appels **API directs** en lecture (`GET`) plutôt que proxy mitmproxy : le
  connecteur n'existe pas encore, donc aucun trafic Odoo→Splynx à intercepter ;
  l'appel direct est plus simple, ciblé et reproductible (cf.
  `docs/splynx-payload-capture.md`).
- Sources observées :
  - `GET /api/2.0/admin/customers/customer` (objet client, live `xiwo`)
  - `GET /api/2.0/admin/customers/customer/{id}/internet-services` (service, live `xiwo`)
  - `GET /api/2.0/admin/customers/customers-online` (monitoring ; schéma officiel
    `CustomerOnlineResponse`, la liste live étant vide faute d'abonné connecté)

## Décisions

### D1 — Champ identité : `name` unique (et non `first_name`/`last_name`)

Splynx expose **un seul champ `name`** sur le client. **MapperV1 concatène**
`first_name` + `last_name` Odoo en `name`. L'ancienne hypothèse de champs séparés
(`field-mappings.md` v1) est **invalidée**.

### D2 — Coordonnées : champ `gps` combiné `"latitude,longitude"`

Splynx stocke les coordonnées dans **un seul champ string** `gps` au format
`"latitude,longitude"` (ex. `"48.856610,2.352220"`), confirmé côté service par
`geo.marker`. MapperV1 compose `gps = f"{geo_lat},{geo_lng}"`. Pas de champs
`latitude`/`longitude` séparés.

### D3 — Traçabilité Odoo : `additional_attributes.odoo_partner_id`

L'ID du partner Odoo est transporté dans `additional_attributes.odoo_partner_id`.
`additional_attributes` est un **objet ouvert** dont les clés sont des champs
**personnalisés configurables par tenant** → MapperV1 ne s'appuie que sur
l'écriture de `odoo_partner_id` et ne présume **aucune** autre clé.

### D4 — Service internet — **Confirmed live 2026-06-23** (POST tenant + doc + 422)

> ✅ **Risque levé.** Le contrat **request** `POST internet-service` est désormais
> figé par triangulation : (a) doc officielle Splynx (`CustomerInternetserviceBase`
> avec `required: [...]`), (b) un **POST 201 réel** sur un tenant (capture
> Story 1.12 / Kelvin 2026-06-23), (c) un **422 « Statut inconnu ! »** sur statut
> bidon confirmant l'enum.

**Endpoint** : `POST /api/2.0/admin/customers/customer/<customer_id>/internet-services` → `201 { "id": <int> }`.

**Champs requis émis par le mapper / binding (8)** — alignés doc + comportement live :

| Champ | Type | Source | Note |
|---|---|---|---|
| `description` | string | nom du produit/offre Odoo | 422 confirmé : « Description est requis ! » si absent |
| `end_date` | string `YYYY-MM-DD` | Odoo ou `"0000-00-00"` (endless) | Doc requis ; live tolère omission — émettre explicitement |
| `login` | string | placeholder `svc_<id>` (Chantier 1, FR-11 = Chantier 2) | « customer login as prefix » recommandé |
| `quantity` | number | défaut 1 | Splynx facture × quantity |
| `start_date` | string `YYYY-MM-DD` | Odoo (défaut = aujourd'hui) | Début facturation |
| `status` | string enum | défaut `"active"` (machine d'états = Story 1.17) | Enum **5 valeurs** (cf. ci-dessous) |
| `taking_ipv4` | number enum string | `"0"`/`"1"`/`"2"` selon `ip_static_mode` | Doc requis ; live tolère omission (défaut `"0"`) |
| `tariff_id` | number | `product.splynx_tariff_id` (résolveur Story 1.12) | `UserError` FR si absent |

**Émis SEULEMENT si renseigné côté Odoo** : `password` (vide acceptable, D3 vindiqué), `ipv4` (si `static`), `mac`, `unit_price`.

**NON émis dans le body** :
- `customer_id` — doc le marque requis mais le **path le porte** ; live 201 a passé sans. Mapper reste pur.
- `geo` (`{address, marker, src}`) — **PAS dans la doc officielle** (présent en lecture seulement). Comportement écriture inconnu → **non émis en 1.12**, spike à tracer.
- `router_id` / `access_device` / `port_id` / `sector_id` — IDs numériques de référentiel hardware Splynx ; le « Serial Number router » Odoo (texte libre) ne mappe pas direct → référentiel hardware = future story.
- `ipv4_pool_id` / `ipv4_route` / `ipv6*` / `discount*` / `bundle_service_id` / `parent_id` / `on_approve` / `top_up_tariff_id` / `unit` / `status_new` / `period` — hors périmètre 1.12.

**Enum `status` — 5 valeurs, source officielle confirmée live** :
`active` · `stopped` · `disabled` · `hidden` · `pending`.

Les valeurs `blocked` / `new` / `inactive` / `Activated` / `terminated` / `draft` apparues dans nos anciens artefacts sont **fausses au niveau service** (elles viennent du modèle customer ou des libellés UI). Le golden PUT existant `status:"disabled"` pour la suspension est CORRECT. Le réalignement de `_bmad-output/specs/spec-axia-isp/service-states.md` est porté par la Story 1.12.

**`taking_ipv4` — enum 3 valeurs** : `"0"` = None (Router assigns) · `"1"` = Permanent (Static IPs) · `"2"` = Dynamic (from IP Pools). → Modélisé en Selection Odoo `ip_static_mode`, pas Bool.

**Découverte transversale** : **la doc sur-déclare**. Plusieurs `required` (`customer_id`, `end_date`, `taking_ipv4`) sont en fait tolérés à l'omission par le backend (le POST live 201 l'a démontré). On émet **explicitement** quand même (clarté + futureproof si Splynx durcit la validation).

> ℹ️ **Goldens read-derived corrigés** : les 16 fichiers
> `splynx_{post,put}_internet_service_*` (4 backends × 2 cas × {POST,PUT}) sont
> **régénérés** sur ce contrat live par la Story 1.12 (Task 7b). Les versions
> originales manquaient `quantity`/`start_date`/`end_date` et (case01) `description`.

### D5 — Monitoring : online = présence dans `customers-online`

Le statut online/offline **n'est pas un champ** : un abonné est *online* s'il
**apparaît** dans la réponse `customers-online`. Mapping lecture seule :
`ipv4 → current_ipv4`, `ipv6`/`ipv6_prefix → current_ipv6`,
`nas_identifier → nas_name`, `time_on`(+`start_session`) `→ uptime`. Aucune
écriture retour. *(Artefact de doc corrigé : la clé réelle est `ipv6_prefix`.)*

> ⚠️ **Provisoire** : le golden `monitoring` est **schéma-dérivé** (liste live
> vide), pas une session observée. `customers-online` est une **liste** ; les
> golden actuels figent **un seul élément** (objet) → **cardinalité à confirmer**
> au 1er appel réel peuplé (les golden passeront en liste si nécessaire).

### D6 — Contrat **uniforme** sur les 4 tenants

`xiwo`, `weelax`, `coqla`, `globalgrid` sont des instances de la **même version
Splynx** (licences distinctes, produit identique). Le **contrat d'API est donc
identique** ; aucune divergence inter-tenant au niveau du schéma. MapperV1 est
**mono-version** (pas de branche par tenant). La seule variation possible est
l'ensemble des **clés custom dans `additional_attributes`** (configuration par
marque) — couvert par D3 (map ouverte). Les golden files par backend partagent
la même structure, valeurs sanitizées.

### D7 — Format & sanitisation des golden files

- Un golden = **objet JSON top-level** = body utile (pas d'enveloppe, pas de dump).
- Nommage : `splynx_<operation>_<backend>_caseNN.json` (`case01` minimal,
  `case02` enrichi). 2 cas × 5 opérations × 4 backends = **40 fichiers**.
- Sanitisation : noms/emails/téléphones = placeholders ; secrets de transport et
  `password` PPP **neutralisés** ; types, casse, formes et optionnels préservés.
- Placeholders d'identité **distincts** (ne pas confondre deux identités) :
  - `__ODOO_PARTNER_ID__` = ID du partner **Odoo**, sous
    `additional_attributes.odoo_partner_id` (customer) ; valeur réelle injectée
    par MapperV1.
  - `__SPLYNX_CUSTOMER_ID__` = clé étrangère **Splynx** `customer_id` (service,
    monitoring) ; c'est l'ID **interne Splynx**, **pas** l'ID Odoo.

### D8 — Champs requis create & refs injectées par backend

Le schéma `CustomerBase` (`POST customer`) exige **`category`, `location_id`,
`name`, `partner_id`**.

> 🔧 **RÉVISION 2026-06-22 (Sprint Change Proposal)** — La formulation initiale
> (« `location_id`/`partner_id` = références **configurées par marque**, injectées
> depuis la config du backend ») est **invalidée** par le 1er test réel contre un
> Splynx live (rejet 422). Vérifié sur la doc Splynx + l'instance XIWO :
> `location_id` et `partner_id` sont des références Splynx **propres à CHAQUE
> client**, **pas** des constantes par marque (une constante mis-taxerait /
> mis-attribuerait les clients). Splynx porte déjà la **géographie** dans un champ
> `State/Province` distinct ; `location` est un **regroupement fiscal/billing
> libre**, `partner` un **revendeur externe**.
>
> **Décision révisée** : on **miroite** ces deux référentiels dans Odoo
> (`axia.splynx.location`, `axia.splynx.partner`), **synchronisés** depuis Splynx
> (`GET /admin/administration/locations`, `GET /admin/partners`) ; on **assigne
> explicitement** une location et un partner **par client** (M2o sur `res.partner`,
> **aucun défaut**) ; un **résolveur** injecte leurs `external_id` dans le payload
> **au moment de la sync** (MapperV1 reste pur). Assignation manquante → **erreur
> Odoo claire** (jamais un 422 opaque). On **ne force aucun mapping** vers un natif
> Odoo sans équivalent Splynx (position fiscale / operating unit **écartées**).
> Implémentation : Stories 1.6 (référentiels) + 1.7 (injection).

**Décision (conservée pour la part mapper)** : **MapperV1 modélise la part
*partner Odoo → payload*** (name, category, contact, adresse, gps,
additional_attributes) ; les refs `location_id`/`partner_id` sont injectées **hors
mapper** par le résolveur de sync (cf. révision ci-dessus). Les golden
`post_customer` **excluent** donc ces deux refs côté mapper (cohérent avec le test
pivot `test_e1_s3` qui appelle `to_splynx_customer(partner)` sans contexte backend).

Enum `customer.status` documenté = `new`, `active`, `blocked`, `disabled` (défaut
`new`). **`terminated` n'y figure pas** → la résiliation (CAP-5, décision métier
`terminated`) opère vraisemblablement au **niveau service**, à confirmer en
Chantier 1.

## Conséquences

- Chantier 1 implémente MapperV1 contre ces golden files (tests de régression
  `test_e1_s3_mapper_v1.py`).
- `field-mappings.md` est réaligné sur ces observations.
- Le timeout HTTPX du client Splynx (Epic 1) sera fixé **explicitement à 10 s**
  (ne pas dépendre du défaut de 5 s).
- Si un futur tenant tourne une **version Splynx différente**, rouvrir cet ADR
  (la prémisse D6 d'uniformité tomberait).

## Limites connues

- La liste `customers-online` live était vide (aucun abonné connecté sur le
  tenant de démo) ; le golden `monitoring` s'appuie sur le **schéma officiel**
  Splynx. À confirmer sur une session réellement active dès que disponible.
- Le contrat **request** `POST customer` est confirmé par le schéma documenté
  `CustomerBase` (champs + requis, cf. D8). Le contrat **request** des services
  internet (`POST/PUT internet-services`) reste dérivé des champs observés en
  lecture (le schéma de body documenté n'a pas été capturé) — à confirmer si
  besoin en Chantier 1.
