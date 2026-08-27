# Procédure de capture des payloads Splynx (POC golden files)

Runbook réutilisable pour capturer, sanitiser et committer les golden files
Splynx du POC (Story 0.2) et pour ajouter de futurs tenants. **Deux méthodes**
sont décrites : **(A) appels API directs** (`curl` + auth `Splynx-EA`) —
**méthode réellement utilisée en Story 0.2**, car le connecteur n'existe pas
encore et il n'y a donc aucun trafic Odoo→Splynx à intercepter ; **(B) mitmproxy
/ mitmdump** pour intercepter le trafic du connecteur une fois celui-ci en place.
Les deux produisent des fichiers JSON exploitables tels quels par les tests
d'acceptation du Chantier 1.

> 🔒 **Secrets hors repo.** Les accès API des 4 tenants (`xiwo`, `weelax`,
> `coqla`, `globalgrid`) ne vivent **jamais** dans le dépôt. `keychain` n'est pas
> disponible upstream en Odoo 18.0 (`third_party_addons/OCA_PINS.txt`) : Story 0.2
> ne résout pas le stockage applicatif des secrets. Les credentials du POC restent
> dans ton environnement local / un gestionnaire externe.

---

## 0. Pourquoi ce format est contraint

Le Chantier 1 charge les golden files via `conftest.load_golden(operation, backend)` :

1. il cherche dans `addons/axia_splynx_connector/tests/golden/` (ou `…/golden_files/`) ;
2. il matche un fichier dès que **le token opération ET le token backend**
   apparaissent dans le nom de fichier ;
3. il fait `json.loads(...)` et attend un **dict top-level** ;
4. `test_e1_s3_mapper_v1.py` compare les **clés top-level** du golden (moins
   `id`, `partner_id`, `added`) avec le payload produit par `MapperV1` ;
5. il exige que l'**ID Odoo** soit traçable dans le payload (via
   `additional_attributes` ou équivalent).

⇒ Tout écart de nommage, toute enveloppe (`{request, response, headers}`), tout
dump brut casse le Chantier 1 ou installe un faux contrat. Respecte §3 et §4.

---

## 1. Pré-requis

- Selon la méthode : `curl` (méthode A, utilisée en Story 0.2) **ou** `mitmproxy`
  (`mitmproxy`, `mitmdump`, `mitmweb` — méthode B). Aucune dépendance Python n'est
  ajoutée au projet pour la capture : ce sont des outils locaux.
- Un compte API dédié au POC pour **chacun** des 4 tenants (lecture/écriture sur
  `customers` et `internet-services`, lecture sur le monitoring).
- L'URL de base de chaque tenant Splynx (`https://<tenant>.splynx…/api/2.0/…`).
- Un jeu de cas de test permettant, par backend :
  - **case01 — minimal** : un client avec les seuls champs requis ;
  - **case02 — enrichi** : un client avec optionnels pertinents
    (`additional_attributes`, coordonnées via le champ combiné `gps`
    `"latitude,longitude"` — cf. ADR D2, pas deux champs séparés —, variantes de
    service internet).

## 2. Matrice à couvrir

5 opérations × 4 backends × ≥ 2 cas = **≥ 40 golden files**.

| Opération              | Sens   | Contenu capturé                         |
|------------------------|--------|-----------------------------------------|
| `post_customer`        | écrit  | body de la requête `POST customer`      |
| `post_internet_service`| écrit  | body de la requête `POST internet-service` |
| `put_customer`         | écrit  | body de la requête `PUT customer`       |
| `put_internet_service` | écrit  | body de la requête `PUT internet-service` |
| `monitoring`           | lit    | body de la **réponse** monitoring       |

> **MAJ Story 1.12 (2026-06-23) — méthode A (écriture) éprouvée.** Story 1.12 a réalisé
> le **premier POST écriture live confirmé** (`POST /api/2.0/admin/customers/customer/<id>/internet-services`,
> 201 sur tenant réel) + un 422 « Statut inconnu ! » sur statut bidon (preuve de
> l'enum 5-valeurs : `active`/`stopped`/`disabled`/`hidden`/`pending`). Les golden
> files internet-service POST/PUT capturés en 0.2 étaient **read-derived** (et donc
> incomplets : manquaient `quantity`/`start_date`/`end_date`) — ils ont été **régénérés
> Task 7b** sur le contrat live confirmé (ADR-001 D4 « Confirmed live »). La méthode A
> (curl direct + auth `Splynx-EA`) est désormais éprouvée pour les opérations
> d'écriture sur les nouveaux tenants — la procédure ci-dessous reste valable.

Backends : `xiwo`, `weelax`, `coqla`, `globalgrid`.

> Le pivot critique du Chantier 1 est `post_customer` sur `xiwo` : assure-toi
> qu'il soit irréprochable.

## 3. Capture des payloads

### 3.A — Méthode A : appels API directs (`curl`) — utilisée en Story 0.2

Tant que le connecteur n'existe pas, il n'y a **aucun trafic Odoo→Splynx** à
intercepter : on interroge directement l'API Splynx en **lecture**. Plus simple,
ciblé et reproductible. Travaille **hors repo** (ex. `~/splynx-capture/`).

L'auth Splynx v2.0 utilise une **signature `Splynx-EA`** (HMAC-SHA256 de
`nonce+key`). Un petit script réutilisable `splynx_get.sh` (hors repo) encapsule
le calcul de signature et l'appel :

```bash
# ~/splynx-capture/splynx_get.sh <base_url> <api_key> <api_secret> <path>
# Lecture seule : client, ses services, et le monitoring
./splynx_get.sh "$XIWO_URL" "$XIWO_KEY" "$XIWO_SECRET" \
  "/api/2.0/admin/customers/customer/{id}"
./splynx_get.sh "$XIWO_URL" "$XIWO_KEY" "$XIWO_SECRET" \
  "/api/2.0/admin/customers/customer/{id}/internet-services"
./splynx_get.sh "$XIWO_URL" "$XIWO_KEY" "$XIWO_SECRET" \
  "/api/2.0/admin/customers/customers-online"
```

> ℹ️ Les bodies **write** (`POST/PUT`) n'ont pas été émis en Story 0.2 (lecture
> seule) : leur contrat est **dérivé** des champs observés en lecture + du schéma
> documenté `CustomerBase`. Émettre de vrais `POST/PUT` les confirmera. De même,
> si `customers-online` est vide, récupère la **forme** depuis le schéma officiel
> et marque le golden comme provisoire (cf. ADR-001, limites).

### 3.B — Méthode B : interception mitmproxy

À privilégier une fois le connecteur en place (capture du trafic réel
Odoo→Splynx, y compris les vrais bodies `POST/PUT`). Travaille dans un répertoire
**hors repo** (ex. `~/splynx-capture/`, jamais sous le dépôt) pour les flux bruts.

```bash
# 1. Enregistrer les flux dans un fichier .flow (HORS repo, jamais committé)
mitmdump -w ~/splynx-capture/xiwo.flow

# 2. Router le trafic du client POC vers le proxy mitmproxy (port 8080 par défaut),
#    en faisant confiance au certificat mitmproxy pour le TLS.
#    Déclenche ensuite les 5 opérations × 2 cas sur le tenant.

# 3. Relire / inspecter hors ligne (aucun appel réseau)
mitmproxy -r ~/splynx-capture/xiwo.flow
```

`mitmdump -w` enregistre les flux ; la relecture `-r` se fait hors ligne, ce qui
permet d'extraire et sanitiser **avant** tout commit. Répète par tenant.

> ⚠️ Les `.flow` bruts contiennent tokens, cookies, `Authorization`, HMAC et PII.
> Ils restent **hors repo**. On n'en extrait que du JSON sanitisé (§4).

Extraction du body utile depuis un flux relu : isole, pour chaque requête/réponse
cible, **uniquement le corps JSON** (pas les headers, pas l'enveloppe HTTP).

## 4. Sanitisation (obligatoire avant commit)

Objectif : partir de données **réelles**, ne committer **aucune** donnée sensible
ou identifiante brute, tout en **préservant la forme du contrat**.

À **supprimer / neutraliser** :

- secrets de transport : header `Authorization`, tokens, cookies, signature HMAC ;
- `Pass ppp` (mot de passe PPP) et tout secret applicatif ;
- PII brute : noms, emails, téléphones, adresses, identifiants clients réels
  → remplacés par des **placeholders structurants** (ex. `"Dupont Jean"`,
  `"j.dupont@test.local"`, `"+33145678901"`).

À **préserver** (valeur de contrat) :

- la **présence** de chaque champ observé, sa **casse**, son **type**
  (un nombre reste un nombre, une string reste une string) ;
- les **listes**, **objets imbriqués** et **optionnels** tels qu'observés
  (`additional_attributes` reste un objet s'il est observé comme objet) ;
- les **divergences inter-tenants** qui ont une valeur de contrat
  (un champ présent chez `xiwo` et absent chez `coqla`, par ex.) — pas les
  valeurs métier elles-mêmes ;
- l'**emplacement de l'ID Odoo transporté** (typiquement sous
  `additional_attributes`), même si la valeur est un placeholder.

Exemples de principe :

- les coordonnées restent dans le **champ combiné `gps`** (string `"lat,lng"`,
  ADR D2), pas deux champs `latitude`/`longitude` séparés ;
- `additional_attributes` reste un objet si observé comme objet ;
- l'ID Odoo reste visible comme emplacement de contrat.

## 5. Nommage et dépôt

Renomme chaque body sanitisé selon la convention **load-bearing** :

```
splynx_<operation>_<backend>_caseNN.json
```

Exemple : `splynx_post_customer_xiwo_case01.json`,
`splynx_post_customer_xiwo_case02.json`, …

Chaque fichier = **un objet JSON top-level** (le body utile, pas d'enveloppe).

Dépose le résultat final dans le chemin canonique :

```
addons/axia_splynx_connector/tests/golden/
```

Un répertoire de travail temporaire `tests/golden/` est toléré pour explorer,
mais le **résultat committé** doit vivre dans
`addons/axia_splynx_connector/tests/golden/`.

## 6. Vérification contractuelle

```bash
# Suite d'acceptation Chantier 0 (volume, couverture, JSON valides, ADR, runbook)
pytest _bmad-output/test-artifacts/atdd-chantier-0/test_e0_s8_splynx_poc_golden_files.py
```

Contrôles attendus :

- ≥ 40 fichiers `.json` valides ;
- chaque couple (opération, backend) couvert par ≥ 1 fichier ;
- au moins un `post_customer` `xiwo` chargeable comme **dict simple** (pivot E1.S3) ;
- aucun secret/PII brut résiduel dans les fichiers committés.

## 7. Après capture — mise à jour des artefacts de référence

Une fois les golden files réels déposés (Voie A de Story 0.2) :

1. réaligner `_bmad-output/specs/spec-axia-isp/field-mappings.md` sur les noms de
   champs **réellement observés** (variations `additional_attributes`, champ
   combiné `gps`, emplacement de l'ID Odoo, écarts inter-tenant) ;
2. rédiger / signer `docs/adr/ADR-001-mapper-payloads-splynx.md` en synthétisant
   les **divergences observées** entre les 4 tenants et en tranchant le contrat
   `MapperV1` (statut `Accepted`).

> Ces deux étapes dépendent des données observées : elles ne doivent pas être
> dérivées d'hypothèses documentaires.

## 8. Ajouter un futur tenant

Reprends §1 → §6 pour le nouveau tenant : nouveau compte API dédié, nouveau
`<backend>` token dans le nommage, ≥ 2 cas par opération, même sanitisation,
dépôt dans le même répertoire. Puis mets à jour ADR-001 si le nouveau tenant
introduit une divergence de contrat.
