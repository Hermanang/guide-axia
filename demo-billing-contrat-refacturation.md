# Guide de démonstration — AXIA ISP · Facturation, Contrat, Refacturation

> Guide fonctionnel de bout en bout du bloc **contrat + facturation** de la
> plateforme AXIA ISP, illustré de captures d'écran validées en environnement
> réel (tenant Coqla, Saint-Martin, EUR).
>
> Il couvre les configurations préalables (fiscalité, résiliation, workflow
> impayés, catalogue offres, utilisateurs) puis le parcours de démonstration
> complet : création client → devis → contrat → activation → compte de
> facturation → première facture → PDF légal DOM-TOM.
>
> Public : commerciaux, chefs de projet fonctionnels, administrateurs
> métier, référents fiscalité.
>
> Un **guide technique compagnon** (`demo-billing-contrat-refacturation-technique.md`)
> regroupe toutes les informations d'environnement, scripts, URLs
> directes, requêtes de contrôle et dépannage serveur — à destination de
> l'équipe d'intégration.

---

## Table des matières

| Section | Durée démo | Contenu |
| --- | --- | --- |
| §1 Vue d'ensemble | 2 min | Public, périmètre, notion d'offre, ce qui est disponible |
| §2 Prérequis | — | Environnement, tenant démo Coqla |
| §3 Connexion + sélection tenant | 1 min | Se connecter et basculer sur Coqla |
| §4 Configuration comptable | 4 min | Taxe TVA 8,5 % + position fiscale |
| §5 Configuration tenant AXIA | 5 min | Signature, résiliation, paiement, motif légitime |
| §6 Configuration workflow impayés | 4 min | Mode suspension, délais, calendriers |
| §7 Catalogue d'offres | 5 min | Fibre 100M, Triple Play, Fibre Pro |
| §8 Utilisateurs et rôles | 3 min | Groupes AXIA, droits par rôle |
| §9 Connexion Splynx | 2 min | Configuration d'un serveur Splynx (optionnel) |
| §10 Démonstration souscription | 8-10 min | Devis → contrat → facturation → PDF |
| §11 Limitations connues | — | Ce qui n'est pas disponible dans la version actuelle |
| §12 Dépannage utilisateur | — | Messages d'erreur courants et parades côté utilisateur |

**Durée totale démo** : 35-45 min (peut être resserrée à 20-25 min en
sautant §6 et §9).

---

## 1. Vue d'ensemble

### 1.1 Sur la notion d'« offre » — mise au point

**Question fréquente** : « Une offre, ce n'est pas un paquet de plusieurs
produits (Fibre + IPTV + Téléphonie) ? »

**Réponse** : Dans la version actuelle, une **offre commerciale est
l'unité vendue au client** — c'est ce qui apparaît sur une ligne de
facture. Elle peut inclure plusieurs services techniques (Internet, TV,
Téléphonie), mais elle est facturée comme un tout indivisible.

Trois façons de proposer un « Triple Play » sont possibles :

| Approche | Comment | Utilisé pour la démo ? |
| --- | --- | --- |
| **Un produit unique nommé** (recommandé) | Créer un produit intitulé `Triple Play — Fibre 300M + TV 4K + Téléphonie` à 49,90 €/mois. Une seule ligne devis, une seule ligne facture. | ✅ Oui — le produit `Triple Play Coqla` de la démo |
| **Plusieurs lignes dans le devis** | Mettre 3 produits contrat séparés dans le devis. Un seul contrat est créé, avec 3 lignes. | Faisable mais non recommandé — l'engagement s'aligne sur la première ligne uniquement |
| **Ajouter une option après souscription** | Assistant **Ajouter option** sur un contrat actif — enrichit avec une ligne supplémentaire | Optionnel (démo étendue) |

**Résultat pratique** : la démo utilise l'approche « produit unique ». Si
un prospect demande « et pour un package, c'est possible ? », la réponse
est : « oui, soit en un produit-bundle nommé, soit en plusieurs lignes de
devis, soit via un avenant après souscription ».

### 1.2 Ce qui est disponible aujourd'hui

| Fonctionnalité | Ce qu'on peut montrer en démo | Statut | Où (§) |
| --- | --- | --- | --- |
| Configuration tenant | Ouvrir la fiche société Coqla : choix du fournisseur de signature, moyen de paiement par défaut, préavis résiliation, politique de pénalité Loi Chatel FR (plafond 25 % après 12 mois), pays du calendrier fériés, politique motif légitime. | ✅ Disponible | §5 |
| Configuration workflow impayés | Menu Paramètres → **AXIA / Workflow impayés** : activer/désactiver globalement, choisir le mode de suspension (immédiat / délai / grâce), régler le délai en jours, activer la période de grâce, bloquer les jours fériés et week-ends. | ✅ Disponible | §6 |
| Catalogue produits (offres) | Créer un produit Service, cocher **Génère un contrat CLM**, saisir la durée d'engagement, attacher la taxe TVA 8,5 %. Montrer les 3 offres pré-provisionnées (Fibre 100M / Triple Play / Fibre 1 Gb Pro). | ✅ Disponible | §7 |
| Position fiscale AXIA | Créer une position fiscale « Saint-Martin (DOM-TOM) » avec le champ **Libellé fiscal AXIA** posé à `TVA 8,5 %` — c'est ce libellé qui apparaît en bas du PDF de facture. | ✅ Disponible | §4.3 |
| Utilisateurs et rôles | Créer un utilisateur commercial dédié, lui affecter les groupes AXIA (Commercial, Billing Manager…) et Odoo (Ventes, Facturation). | ✅ Disponible | §8 |
| Configuration Splynx | Créer/éditer un serveur Splynx (nom, URL, clé API), saisir les secrets (chiffrement automatique), lancer **Ping** et **Synchroniser locations**. | ⚠️ Fonctionnel mais serveurs démo pointent vers des URLs de test | §9 |
| Devis → contrat automatique | Sur un devis contenant une offre contrat, cliquer **Confirmer** : un contrat est créé automatiquement à l'état **À signer**. Un bouton **Contrats CLM** apparaît sur le devis. | ✅ Disponible | §10.2-3 |
| Machine d'états contrat | Contrat : **Brouillon → À signer → Signé → Actif → Résilié → Archivé** (état final immuable). Boutons d'action visibles en haut de la fiche : Envoyer pour signature, Activer, Résilier, Archiver, Annuler. | ✅ Disponible | §10.3-4 |
| PDF contractuel | Bouton **Imprimer → Contrat AXIA** sur la fiche contrat — génère un PDF avec mentions Loi Chatel, engagement, prix TTC. | ✅ Disponible | §10 (bouton Imprimer) |
| Signature manuelle scannée | Assistant **Téléverser scan signé** sur un contrat en attente de signature : upload d'un PDF signé manuscritement → passage à **Signé** avec pièce jointe traçable. | ✅ Disponible | §10 optionnel |
| Compte de facturation automatique | Après activation d'un contrat, un compte de facturation apparaît dans **AXIA — RBM → Comptes de facturation** avec numéro `BILL-000XXX`, statut **Actif**, lié au contrat. | ✅ Disponible | §10.5 |
| Facture prorata + PDF fiscal DOM-TOM | Créer une facture dans **AXIA — RBM → Factures récurrentes** avec période 22-31/08, type **Première facture (prorata)** → validation → **PDF en euros avec position fiscale, libellé « TVA 8,5 % » et mention légale DOM-TOM.** | ✅ Disponible | §10.6-7 |
| Traçabilité des événements | Menu Paramètres → Technique → Audit AXIA : chaîne complète des événements liés à un contrat (création, changements d'état, création du compte de facturation, création de la facture). | ✅ Disponible | §10.8 |
| Avenant / changement d'offre | Assistant **Ajouter option** ou **Upgrade** sur un contrat actif : nouveau produit + date d'effet → ligne ajoutée + événement tracé. | ✅ Disponible | §10 optionnel |
| Résiliation Loi Chatel | Assistant **Résilier** : motif « Contractuel — Loi Chatel », le préavis est calculé automatiquement (jours fériés FR intégrés) → statut passe à **Résilié**. | ✅ Disponible | §10 optionnel |
| Résiliation motif légitime | Assistant résiliation avec motif « Légitime » (déménagement, force majeure) → validation par un opérateur habilité visible dans **Contrats → Validations motifs légitimes**. | ✅ Disponible | §10 optionnel |
| Motif opérateur | Champ dérogation immuable après enregistrement — toute modification exige une nouvelle action, traçabilité complète préservée. | ✅ Disponible | §10 optionnel |
| Workflow impayés | Tâche automatique **Détection impayés** (toutes les 15 min) qui scanne les factures échues et crée une décision de suspension respectant délai, grâce, calendrier. | ✅ Disponible | Requiert une facture échue |
| Réactivation 24/7 sur paiement | À la réception d'un paiement, réactivation automatique (même week-end / jour férié si l'option est activée). | ✅ Disponible | Requiert un contrat suspendu |
| Interrupteur global workflow impayés | Décocher **Activer les suspensions** dans les paramètres → plus aucune suspension programmée (utile en cas d'incident majeur). | ✅ Disponible | §6.1 |
| **Cycle mensuel automatique des factures** | Tâche quotidienne nocturne (03 h, fuseau du tenant) qui génère les factures récurrentes aux jours anniversaire des comptes de facturation. Désactivée par défaut, à activer après configuration. | ✅ Disponible | §11.2 |
| **1ʳᵉ facture générée à l'activation du contrat** | À l'activation d'un contrat, la première facture prorata est créée automatiquement (sans intervention manuelle). | ⚠️ Livré, correctif de compatibilité en cours pour l'environnement de démonstration | §10.6 |
| **Archivage automatique des contrats terminés** | Tâche quotidienne (03 h 05) qui fait basculer les contrats **Résilié** vers **Archivé** après un délai configurable (30 jours par défaut). État Archivé immuable. | ✅ Disponible | §5.6 · §10.9 |
| **Pénalité forfaitaire (flat fee)** | Résiliation avec pénalité fixe configurable par tenant (montant + devise). Cohabite avec la Loi Chatel FR (choix par tenant). | ✅ Disponible | §5.3 |
| **Relances impayés automatiques** | Politique de dunning en cours de développement — visible en démo technique uniquement. | ❌ En cours | §11.3 |
| **Calendrier des jours fériés** | Pas de menu Odoo pour lister/éditer les jours fériés — configuré via le pays du tenant. | ❌ Pas d'interface | §11.4 |
| **Connexion Splynx réelle** | Les serveurs Splynx de démonstration pointent vers des URLs de test — utile en démo technique pour montrer la mécanique, mais pas l'appel réel. | ⚠️ Test uniquement | §11.5 |
| **Portail client self-service** | Pas d'espace client pour consulter les factures ou signer en ligne — toute action passe par le back-office. | ❌ Non prévu | §11.7 |

---

## 2. Prérequis

La démonstration se déroule sur le tenant **Coqla** :

- Société : **Coqla**
- Devise : **EUR**
- Pays : **Saint-Martin (partie française)**
- Régime fiscal : DOM-TOM (TVA 8,5 %)

Le tenant Coqla est prêt à l'emploi avec :

- Plan comptable installé
- Taxe **TVA 8,5 % (Saint-Martin/DOM-TOM)** créée et attachée aux
  produits
- Position fiscale **Saint-Martin (DOM-TOM)** avec libellé fiscal AXIA
  posé à `TVA 8,5 %` et mapping automatique TVA 20 % → 8,5 %
- 3 offres commerciales pré-provisionnées (Fibre 100M, Triple Play,
  Fibre 1 Gb Pro)
- 11 paramètres tenant configurés (signature, résiliation, workflow
  impayés)

Un compte administrateur pré-configuré permet d'accéder à tous les
menus AXIA (Commercial, Billing Manager, Administrateur AXIA) ainsi
qu'aux menus Odoo standard (Ventes, Facturation).

*Pour la mise en place initiale de l'environnement, l'installation
serveur et le provisionnement d'une base fraîche pour une démo client
formelle, voir le guide technique compagnon.*

---

## 3. Étape 1 — Connexion et sélection du tenant Coqla

### 3.1 Connexion

Ouvrir l'écran de connexion Odoo dans le navigateur.

![Écran de connexion Odoo](images/demo/01-login.png)

Saisir l'identifiant et le mot de passe du compte administrateur
préparé pour la démonstration.

### 3.2 Basculer sur le tenant Coqla

En haut à droite de l'écran, cliquer sur le sélecteur de société et
choisir **Coqla**.

**Point de contrôle** : le sélecteur affiche « Coqla » ; toutes les
créations suivantes se feront dans ce contexte.

![Sélecteur de société sur Coqla](images/demo/03-coqla-selected.png)

L'écran d'accueil affiche les modules disponibles :

![Page d'accueil — modules disponibles](images/demo/28-app-switcher-home.png)

---

## 4. Étape 2 — Configuration comptable (taxe + position fiscale)

Cette étape est obligatoire pour la démo : sans taxe TVA 8,5 % attachée
aux produits, la facture affiche une taxe par défaut incohérente avec le
régime DOM-TOM.

### 4.1 Vérifier le plan comptable

**Menu** : `Facturation → Configuration → Plans de comptes`

Le plan comptable générique est installé sur Coqla. Un journal de vente
`Customer Invoices (INV)` existe.

**Point de contrôle** : `Facturation → Configuration → Journaux` — un
journal `Customer Invoices` de type **Vente**, code `INV`.

### 4.2 Créer la taxe TVA 8,5 %

**Menu** : `Facturation → Configuration → Taxes → Nouveau`

![Liste des taxes de vente](images/demo/09-taxes-list.png)

Après création, la fiche de la taxe ressemble à :

![Fiche taxe TVA 8,5 %](images/demo/10-tax-tva85-form.png)

| Champ | Valeur |
| --- | --- |
| Nom de la taxe | `TVA 8,5% (Saint-Martin/DOM-TOM)` |
| Type de taxe | Ventes |
| Type de calcul | Pourcentage du prix |
| Montant | 8.5 |
| Onglet **Avancé** → Étiquette sur la facture | `TVA 8,5 %` |
| Groupe de taxes | `TVA 8,5 %` |

**Note importante sur le groupe de taxes** : Odoo agrège les totaux d'une
facture par **nom de groupe de taxes**. Il est important que ce groupe
s'appelle explicitement `TVA 8,5 %` et pas le nom générique par défaut
(`VAT 0%`) sinon les totaux affichent un libellé trompeur.

### 4.3 Créer la position fiscale (avec libellé fiscal AXIA)

**Menu** : `Facturation → Configuration → Positions fiscales → Nouveau`

![Liste des positions fiscales](images/demo/11-fiscal-positions-list.png)

Fiche de la position fiscale — noter le champ **Libellé fiscal AXIA**
posé à `TVA 8,5 %` et le mapping automatique dans l'onglet
**Correspondance de taxes** :

![Fiche position fiscale Saint-Martin avec libellé AXIA + mapping taxes](images/demo/12-fiscal-position-saint-martin.png)

| Champ | Valeur |
| --- | --- |
| Nom de la position | `Saint-Martin (DOM-TOM)` |
| **Libellé fiscal AXIA** | `TVA 8,5 %` |
| Détecter automatiquement | ✅ coché |
| Pays | Saint-Martin (partie française) |
| Société | Coqla |

**Correspondance de taxes** (onglet) : une ligne mappe la TVA 20 %
métropole vers la TVA 8,5 % Saint-Martin. Ce mapping permet d'utiliser
la même taxe source dans le catalogue produit central : la position
fiscale la traduit automatiquement au moment du devis selon le pays du
client.

**Point de contrôle** : ouvrir la fiche, vérifier que le champ **Libellé
fiscal AXIA** est visible et que l'onglet **Correspondance de taxes**
contient au moins une ligne.

---

## 5. Étape 3 — Configuration tenant AXIA

**Menu** : `Configuration → Sociétés → Sociétés → Coqla`

![Liste des sociétés](images/demo/04-companies-list.png)

Les configurations AXIA sont présentées sous forme de **sections**
directement dans la fiche société (pas dans des onglets séparés). En
scrollant on trouve les blocs « AXIA — Configuration signature »,
« AXIA — Facturation par défaut », « AXIA — Résiliation », etc. :

![Fiche société Coqla — sections AXIA](images/demo/05-company-coqla-form.png)

### 5.1 Section « AXIA — Configuration signature »

| Champ | Valeurs possibles | Démo Coqla |
| --- | --- | --- |
| Fournisseur de signature | Signature électronique · Signature manuscrite scannée | **Signature manuscrite scannée** |

### 5.2 Section « AXIA — Facturation par défaut »

| Champ | Valeurs possibles | Démo Coqla |
| --- | --- | --- |
| Mode de paiement par défaut | SEPA prélèvement · Virement · Chèque · Espèces · Carte | **SEPA prélèvement** |

### 5.3 Section « AXIA — Résiliation »

| Champ | Démo Coqla | Signification |
| --- | --- | --- |
| Préavis résiliation (jours) | **30** | Préavis calendaire minimum |
| Politique de pénalité | **Loi Chatel FR — plafond 25 % après M+12** | Pénalité plafonnée à 25 % du reste dû à partir du 13ᵉ mois |
| Plafond pénalité (%) | 25 | Plafond en pourcentage (si applicable) |
| Plafond appliqué à partir du mois | 12 | Mois à partir duquel le plafond entre en vigueur |
| Montant pénalité forfaitaire | (défaut vide) | Alternative : pénalité fixe (utile pour marchés SN, ML — ex. 30 000 FCFA) |
| Devise pénalité forfaitaire | (défaut vide) | Devise de la pénalité forfaitaire |
| Pays du calendrier fériés | **FR** | Pays de référence pour les jours fériés |
| Subdivision DOM-TOM | 971 (option) | Guadeloupe = 971, Martinique = 972, etc. |
| Politique motif légitime | **Activée (workflow validation opérateur requis)** | Résiliation sans pénalité possible après validation opérateur |

**Note démo — pénalité forfaitaire vs Loi Chatel** : sur les marchés où la
Loi Chatel FR ne s'applique pas (Sénégal, Mali), un tenant peut basculer
en pénalité forfaitaire : montant fixe unique (par exemple 30 000 FCFA)
plutôt que le calcul « reste dû plafonné 25 % ». Les deux modes
cohabitent dans le code — l'admin choisit par tenant.

**Point démo** : ces champs matérialisent la conformité juridique locale
— Loi Chatel FR, jours fériés adaptés à Saint-Martin, motif légitime
(déménagement à l'étranger, force majeure) soumis à validation
opérateur.

### 5.4 Section « AXIA — Suspension (approbation) »

| Champ | Signification |
| --- | --- |
| Mode d'approbation avant suspension | Automatique / manuel / hybride |
| Timeout d'attente approbation (heures) | Délai avant escalade |
| Seuil auto-approbation (mode hybride) | Nombre de jours au-delà duquel l'approbation devient automatique |

### 5.5 Section « AXIA — Archivage »

| Champ | Démo Coqla | Signification |
| --- | --- | --- |
| Délai d'archivage (jours) | **30** | Nombre de jours après résiliation avant archivage automatique. Typique : 30 (SN), 60 (FR), 90 (NC). |

**Fonctionnement** : une tâche quotidienne (03 h 05, fuseau du tenant)
scanne les contrats en statut **Résilié** dont la date effective de fin
est antérieure à `aujourd'hui − N jours`. Chaque contrat concerné passe à
l'état **Archivé**. Cet état est **immuable** — aucune modification n'est
plus possible sur le contrat (protection légale et intégrité de
l'historique).

### 5.6 Section « AXIA — Facturation par cycle »

| Champ | Démo Coqla | Signification |
| --- | --- | --- |
| Journal comptable AXIA | Ventes Abonnements AXIA | Journal de vente dédié à la facturation récurrente AXIA, distinct du journal Odoo natif |

Un journal `Ventes Abonnements AXIA` est provisionné automatiquement à
la première utilisation pour chaque tenant. Il porte sa propre séquence
de numérotation avec garanties de conformité fiscale FR (numérotation
continue sans trou).

### 5.7 Champs Odoo natifs utiles

- **Devise** : EUR (Coqla)
- **Pays** : Saint-Martin (partie française)
- **Journal de vente par défaut** : Customer Invoices (INV)
- **Séquence de facture** : générée automatiquement par Odoo
  (`INV/YYYY/00001`)

---

## 6. Étape 4 — Configuration du workflow impayés

**Menu** : `Configuration → Paramètres généraux → AXIA / Workflow impayés`
(visible uniquement pour les utilisateurs administrateurs AXIA)

![Paramètres — sidebar avec « AXIA / Workflow impayés »](images/demo/07-settings-root.png)

En cliquant sur **AXIA / Workflow impayés** dans la barre latérale, les
sections de configuration apparaissent (activation, délais, calendriers) :

![Paramètres AXIA Workflow impayés](images/demo/08-settings-axia-workflow.png)

### 6.1 Section « Activation »

| Champ | Démo Coqla | Signification |
| --- | --- | --- |
| Activer les suspensions | ✅ | Interrupteur global du workflow |
| Statut factures échues à considérer | (défaut) | Filtre sur les factures à surveiller |

### 6.2 Section « Délais et grâce »

| Champ | Démo Coqla | Signification |
| --- | --- | --- |
| Mode de suspension | **Délai (attendre N jours après échéance)** | Immédiat / délai / période de grâce |
| Délai avant suspension (valeur) | **15** | Nombre de jours après échéance |
| Unité du délai | Jour | Seule unité disponible |
| Autoriser période de grâce | ✅ | Grâce supplémentaire après le délai |
| Jours de grâce | (défaut) | Nombre de jours supplémentaires |

### 6.3 Section « Calendrier week-ends »

| Champ | Signification |
| --- | --- |
| Bloquer les suspensions le samedi | Reporter les suspensions programmées un samedi |
| Bloquer les suspensions le dimanche | Idem pour le dimanche |
| Autoriser les réactivations le week-end | Permettre la remise en service même le week-end |

### 6.4 Section « Calendrier jours fériés »

| Champ | Signification |
| --- | --- |
| Bloquer les suspensions les jours fériés | Reporter au jour ouvré suivant |
| Autoriser les réactivations les jours fériés | Permettre la remise en service même un jour férié |
| Source pays des fériés | Automatique (depuis la société) ou manuelle |

> **Limitation** : le calendrier des jours fériés lui-même n'a pas
> d'interface Odoo dédiée. Les fériés sont résolus automatiquement selon
> le pays configuré ici et dans §5.3. Voir §11.4.

### 6.5 Section « Déduplication anti-doublons »

| Champ | Signification |
| --- | --- |
| Détection floue de doublons | Repérer les contacts similaires (fautes de frappe, variations) |

---

## 7. Étape 5 — Catalogue d'offres

C'est le cœur d'une démo commerciale. On montre comment créer une offre,
puis on présente les 3 offres pré-provisionnées.

### 7.1 Où voir et créer un produit ?

**Menu** : `Ventes → Produits → Produits` (ou `Facturation → Clients →
Produits`).

![Liste des produits — 6 offres visibles (vue Kanban)](images/demo/13-products-list.png)

### 7.2 Les 3 offres Coqla pré-provisionnées

| Nom commercial | Prix HT | Engagement | Type |
| --- | --- | --- | --- |
| Fibre Coqla 100M — Engagement 12 mois | **29,90 €** | 12 mois | Offre standard |
| Triple Play Coqla — Fibre 300M + TV 4K + Téléphonie illimitée | **49,90 €** | 24 mois | Bundle (un produit = une offre indivisible) |
| Fibre Coqla 1 Gb Pro — Sans engagement | **79,90 €** | 0 mois | Offre pro sans engagement |

### 7.3 Créer un nouveau produit — pas-à-pas

Cliquer **Nouveau** dans la liste des produits.

**Onglet Général** :

| Champ | Valeur |
| --- | --- |
| Nom | `Fibre Coqla 500M — Engagement 12 mois` |
| Type de produit | Service |
| Prix de vente | 49.90 |
| Peut être vendu | ✅ |
| Peut être acheté | (décoché) |

**Onglet Ventes — section AXIA CLM** :

| Champ | Valeur |
| --- | --- |
| **Génère un contrat CLM** | ✅ |
| **Engagement (mois)** | 12 |
| Description commerciale | `Fibre 500 Mbps symétrique — Installation offerte` |

**Onglet Facturation** :

| Champ | Valeur |
| --- | --- |
| Politique de facturation | Quantités commandées |
| Taxes clients | `TVA 8,5% (Saint-Martin/DOM-TOM)` |

Enregistrer. Le produit est prêt à figurer dans un devis.

### 7.4 Aperçus des onglets de la fiche produit

Onglet Général de la fiche Triple Play :

![Fiche produit Triple Play — onglet Général](images/demo/14b-product-general-tab.png)

Onglet Ventes avec la section **AXIA CLM** clairement identifiée :

![Fiche produit Triple Play — onglet Ventes avec section AXIA CLM](images/demo/15-product-triple-play-sales-tab.png)

Points de contrôle démo :
- **Le champ Engagement (mois)** n'apparaît que si **Génère un contrat CLM**
  est coché (affichage conditionnel)
- Si l'option est décochée, le devis passera bien à l'état confirmé mais
  **aucun contrat ne sera créé**

### 7.5 Limitations du catalogue actuel

- **Pas de type « pack multi-produits »** : un pack Triple Play est un
  produit unique nommé (voir §1.1)
- **Pas d'options techniques catalogue** : les options s'ajoutent après
  souscription via l'assistant **Ajouter option**
- **Pas de tarification par palier** (dégressivité)

---

## 8. Étape 6 — Utilisateurs et rôles

### 8.1 Les groupes AXIA disponibles

**Menu** : `Configuration → Utilisateurs et sociétés → Groupes` (filtre
« AXIA »)

![Liste des utilisateurs](images/demo/25-users-list.png)

Fiche utilisateur admin (sociétés autorisées Coqla + My Company) :

![Fiche utilisateur admin](images/demo/26-user-admin-form.png)

Onglet **Droits d'accès** — visualisation des groupes affectés :

![Onglet Droits d'accès — groupes AXIA + Ventes/Facturation](images/demo/27-user-access-rights.png)

| Groupe | Rôle |
| --- | --- |
| AXIA / Commercial | Créer des contrats depuis les devis |
| AXIA / Administratif | Opérations quotidiennes, réactivations |
| AXIA / Contentieux | Suspensions et réactivations d'exception |
| AXIA / Administrateur Odoo | Accès aux paramètres AXIA et boutons techniques |
| AXIA / Opérateur habilité résiliation | Valider les motifs légitimes de résiliation |
| AXIA / Sync Admin | Synchronisation Splynx |
| AXIA / Audit Admin | Consulter la traçabilité des événements |
| AXIA — Billing Manager | Accès au menu **AXIA — RBM** (comptes de facturation, factures) |

### 8.2 Créer un utilisateur démo (persona commercial)

**Menu** : `Configuration → Utilisateurs et sociétés → Utilisateurs →
Nouveau`

| Champ | Valeur |
| --- | --- |
| Nom | Emma LAURENT (Commercial Coqla) |
| Email de connexion | emma.laurent@coqla.sxm |
| Société par défaut | Coqla |
| Sociétés autorisées | Coqla |
| Onglet **Droits d'accès** | Ventes / Utilisateur, AXIA / Commercial, Facturation / Facturation, AXIA — Billing Manager |

Enregistrer et envoyer l'invitation.

### 8.3 Politique de rôles

La version actuelle utilise un ensemble de groupes techniques minimum. La
définition des 7 rôles produit finaux (Commercial, Contentieux,
Comptable, Ops, Direction, Administrateur, Audit) sera configurable via
l'interface administrateur dans une évolution ultérieure.

---

## 9. Étape 7 — Connexion Splynx (optionnel démo tech)

**Menu** : `Splynx → Serveurs Splynx → Nouveau`

> Sur la base de démonstration, les serveurs Splynx pré-configurés
> pointent vers des URLs de test. Ne pas cliquer **Ping** en démo métier
> — sauf public technique curieux de la mécanique.

### 9.1 Champs à montrer

| Champ | Valeur exemple | Notes |
| --- | --- | --- |
| Nom | Coqla Splynx sandbox | Libre |
| URL Splynx | `https://splynx.coqla.sxm` | URL du serveur Splynx du tenant |
| Clé API publique | `xxx...` | Générée dans Splynx (Admin → API keys) |
| Secret API | Saisi via assistant | Chiffré automatiquement à l'enregistrement |
| Secret webhook | Saisi via assistant | Chiffré automatiquement |
| Fuseau horaire | America/Marigot | Pour l'interprétation des dates renvoyées par Splynx |

### 9.2 Boutons disponibles (administrateur AXIA uniquement)

- **Ping** — test de connectivité authentifié
- **Synchroniser locations / revendeurs** — import des référentiels
- **Importer les pools IP** — assistant IPAM

### 9.3 Sécurité des secrets

Les secrets d'API et webhooks ne sont **jamais stockés en clair**. Ils
sont chiffrés à l'enregistrement grâce à une clé maître injectée hors
base de données. La révélation en clair passe par un assistant dédié,
tracé dans l'audit.

---

## 10. Démonstration souscription de bout en bout

**Contexte narratif** : Emma (commerciale Coqla) reçoit une prospect
intéressée par le Triple Play (49,90 € / 24 mois d'engagement) — Sophie
MARTIN, résidente à Marigot (Saint-Martin, DOM-TOM, TVA 8,5 %). Elle
génère le devis, la cliente signe, le contrat s'active, un compte de
facturation est provisionné automatiquement, et la première facture
prorata (22 → 31 août) est éditée.

**Durée** : 8-10 min. **Menus utilisés** : Contacts, Ventes, Contrats,
AXIA — RBM.

### 10.1 Créer le client

**Menu** : `Contacts → Nouveau`

| Champ | Valeur |
| --- | --- |
| Type | Individuel |
| Nom | Sophie MARTIN |
| Email | sophie.martin@example.com |
| Téléphone | +590 590 40 00 00 |
| Rue | 8 boulevard de Grand-Case |
| Ville | Marigot |
| Code postal | 97150 |
| Pays | Saint-Martin (partie française) |
| Société | Coqla |

Enregistrer.

### 10.2 Créer le devis

**Menu** : `Ventes → Devis → Nouveau`

![Liste des devis](images/demo/16-quotes-list.png)

Nouveau devis (formulaire vide) :

![Nouveau devis](images/demo/17-quote-new-empty.png)

| Champ | Valeur |
| --- | --- |
| Client | Sophie MARTIN |
| Position fiscale | Détectée automatiquement → Saint-Martin (DOM-TOM) |
| Ligne d'article | Triple Play Coqla — Fibre 300M + TV 4K + Téléphonie illimitée |
| Quantité | 1 |

Le total s'affiche : **49,90 HT · TVA 8,5 % 4,24 · TTC 54,14 €**.

Enregistrer → un numéro `S000XX` est attribué.

### 10.3 Confirmer le devis → contrat automatique

Cliquer **Confirmer**.

Ce qui se passe :

1. Le devis passe à l'état **Commande confirmée**
2. Le système détecte qu'une ligne du devis est une offre contrat
3. Un contrat est créé automatiquement avec :
   - Numéro : `CTR-000003` (séquence propre à Coqla)
   - Statut : **À signer** (une offre contrat saute directement à cette
     étape, on n'attend pas de brouillon manuel)
   - Devis d'origine : la référence au devis est conservée

**Point de contrôle** : sur la vue du devis, un **bouton « Contrats CLM »**
apparaît en haut à droite avec le compteur **1**.

Cliquer dessus → le contrat créé est visible.

### 10.4 Activer le contrat

Ouvrir le contrat `CTR-000003` — menu `Contrats → Contrats` ou via le
bouton du devis.

![Liste des contrats](images/demo/18-contracts-list.png)

Fiche contrat (barre d'état 6 statuts, boutons **Activer / Résilier /
Archiver** en haut) :

![Fiche contrat — barre d'état + boutons](images/demo/19-contract-form.png)

**Vue attendue** :
- Barre d'état : **Brouillon → À signer → Signé → Actif → Résilié →
  Archivé**
- Boutons d'action : **Envoyer pour signature** · **Activer** ·
  **Résilier** · **Archiver** · **Annuler**
- Onglet **Contenu** : 1 ligne = Triple Play (référence produit + prix)
- Onglet **Discussion** : événements liés au contrat

Cliquer **Activer**. Cela déclenche :

1. Passage du statut **À signer** à **Actif**
2. Émission automatique de 4 ordres vers le module de facturation :
   - **Création du compte de facturation** — provisionne `BILL-000XXX`
   - **Application de la politique de facturation** — configure le cycle
     (jour anniversaire, mode de prorata) **et génère la 1ʳᵉ facture
     prorata**
   - **Application de la politique de relance** — configure les paliers
     de dunning
   - **Notification de l'activation** — pour l'orchestration Splynx

**Point de contrôle** : la barre d'état passe visuellement à **Actif**
(en vert).

### 10.5 Vérifier le compte de facturation créé

**Menu** : `AXIA — RBM → Comptes de facturation`

![Liste des comptes de facturation](images/demo/20-billing-accounts-list.png)

Après 3-5 secondes (le temps que le compte soit provisionné en arrière-
plan), un nouveau compte apparaît :

| Numéro | Statut | Devise |
| --- | --- | --- |
| **BILL-000003** | Actif | EUR |

Cliquer dessus pour ouvrir la fiche :

![Fiche du compte de facturation](images/demo/21-billing-account-form.png)

- Numéro : BILL-000003 (séquence propre à chaque tenant)
- Statut : **Actif** (statuts possibles : Brouillon → Actif → Suspendu →
  En clôture → Clos)
- Devise : EUR
- **Jour de facturation** : jour du mois où sera émise la facture
  récurrente (déduit de la date d'activation)
- **Mode de prorata** : `Jour` (calcul au prorata journalier)
- **Date du prochain cycle** : date de génération de la prochaine facture
  mensuelle
- **Index du dernier cycle** : numéro du dernier cycle facturé (1 =
  première facture prorata, 2+ = cycles complets)
- **Prix mensuel de substitution** : optionnel — pour surcharger le prix
  standard du produit sur ce compte (remises négociées commerciales)

### 10.6 La première facture est créée automatiquement

À l'activation du contrat, la première facture **prorata** est générée
automatiquement dans le journal `Ventes Abonnements AXIA` du tenant.
Elle apparaît directement dans le menu `AXIA — RBM → Factures récurrentes`
au statut **Comptabilisé**.

> ⚠️ **Sur l'environnement de démonstration actuel** : un correctif de
> compatibilité est en cours pour rendre cette génération automatique
> pleinement opérationnelle. En attendant, la première facture peut être
> créée à la main selon la procédure ci-dessous.

**Procédure manuelle (parade temporaire)** — menu `AXIA — RBM →
Factures récurrentes → Nouveau`

![Liste des factures récurrentes AXIA](images/demo/22-invoices-recurring-list.png)

Fiche facture (onglets **Lignes de facture**, **Écritures comptables**,
**Autres informations**, **AXIA RBM**) :

![Fiche facture](images/demo/23-invoice-recurring-form.png)

Onglet **AXIA RBM** — les métadonnées de facturation :

![Onglet AXIA RBM sur la facture](images/demo/24-invoice-axia-rbm-tab.png)

| Champ | Valeur |
| --- | --- |
| Journal | Customer Invoices (défaut Coqla) |
| Client | Sophie MARTIN |
| Position fiscale | Saint-Martin (DOM-TOM) |
| Date de facture | 22/08/2026 |
| **[Onglet AXIA RBM]** | |
| Compte de facturation | BILL-000003 |
| Début de période | 22/08/2026 |
| Fin de période | 31/08/2026 |
| Numéro de cycle | 1 |
| Type de facture | Première facture (prorata) |
| **[Onglet Lignes de facture]** | |
| Article | Triple Play Coqla |
| Quantité | 1.00 |
| Prix unitaire | 16.10 (calcul : 49,90 × 10/31 = 16,10) |
| Description | Prorata 22-31/08/2026 (10 jours) |
| Taxes | TVA 8,5 % (Saint-Martin/DOM-TOM) (appliquée automatiquement par la position fiscale) |

Enregistrer → facture en **Brouillon**.

Cliquer **Valider** → passage à **Comptabilisé**, numéro `INV/2026/00001`
attribué automatiquement.

**Totaux à droite** : HT **16,10 €** · TVA 8,5 % **1,37 €** · **Total
TTC 17,47 €**.

Le libellé fiscal `TVA 8,5 %` est résolu automatiquement depuis la
position fiscale.

### 10.7 Imprimer le PDF

Sur la facture validée, cliquer **Imprimer → Facture AXIA (récurrente)**.

Sections attendues du PDF :

1. **En-tête** : `Facture INV/2026/00001`
2. **Société émettrice** : Coqla · Saint-Martin (partie française) ·
   Date d'émission 22/8/2026 · Devise **EUR** · Position fiscale
   Saint-Martin (DOM-TOM)
3. **Client** : Sophie MARTIN · adresse · email
4. **Période et type** : du 22/8/2026 au 31/8/2026 · Type **Première
   facture (prorata)** · Cycle n° 1 · Compte de facturation BILL-000003
5. **Détail des prestations** : ligne Triple Play · 1,00 · 16,10 € · TVA
   8,5 % (Saint-Martin/DOM-TOM) · 16,10 €
6. **Totaux** : Total HT **16,10 €** · TVA 8,5 % **1,37 €** · **Total
   TTC 17,47 €**
7. **Mention légale conditionnelle** : « *Facture DOM-TOM — TVA 8,5 %
   (loi de finances DOM-TOM, taux réduit outre-mer).* »

Le PDF s'adapte au pays de la société :
- FR métropole → « TVA 20 % »
- DOM-TOM → « TVA 8,5 % » + mention DOM-TOM
- Nouvelle-Calédonie → « TGC 11 % » (Taxe Générale à la Consommation, pas
  de TVA)
- Sénégal → « TVA 18 % »

### 10.8 Cycle mensuel automatique (après la 1ʳᵉ facture)

Une fois la première facture prorata émise, une tâche quotidienne
nocturne (03 h, fuseau du tenant) scanne les comptes de facturation et
génère automatiquement les factures récurrentes aux jours anniversaire.

**À montrer en démo** : `Configuration → Technique → Tâches planifiées →
AXIA RBM — Billing Cycle Dispatcher`

- Type : quotidien à 03 h
- Statut par défaut : **désactivée** (activation manuelle après
  configuration initiale, choix de sécurité pour éviter tout batch
  imprévu sur un tenant en cours de setup)
- Une fois activée : pour chaque compte de facturation actif dont la
  **Date du prochain cycle** est atteinte, une facture au type **Facture
  récurrente cycle** est créée, validée et postée automatiquement

**Point démo à souligner** : ce comportement suit le standard des grands
FAI (Free, Orange, SFR) — batch nocturne quotidien, pas d'émission de
facture en journée pour éviter la charge sur les serveurs de production.

### 10.9 Archivage automatique J+30

Une deuxième tâche quotidienne (03 h 05) fait basculer automatiquement
les contrats **Résilié** vers **Archivé** après un délai configurable
(par défaut 30 jours — voir §5.5).

- **Menu** : `Configuration → Technique → Tâches planifiées → AXIA CLM —
  Archive Terminated Contracts (J+30)`
- **Actif par défaut** : oui
- **Comportement** : le contrat garde toutes ses données historiques
  mais devient **immuable** (aucune modification n'est plus autorisée —
  ni sur le contrat, ni sur ses lignes, ni sur les métadonnées).
- **Traçabilité** : chaque archivage produit un événement
  `contract_archived` dans l'audit avec un identifiant de corrélation
  neuf (distinct de celui de la résiliation initiale).

### 10.10 Consulter l'audit trail (démo technique optionnelle)

**Menu** : `Configuration → Technique → Audit AXIA → Événements`
(nécessite le groupe **AXIA / Audit Admin**)

![Liste des événements d'audit AXIA](images/demo/30-audit-events-list.png)

Un contrat activé produit une chaîne linéaire de ~8 événements tracés :
création du contrat, changements d'état, ordres émis vers le module de
facturation, création du compte de facturation, création de la facture
en brouillon. Chaque événement est rattaché à un identifiant de
corrélation unique qui remonte au point d'entrée (le devis confirmé).

---

## 11. Limitations connues (version actuelle)

### 11.1 Pas de type « pack multi-produits »

Un pack Triple Play est un **produit unique nommé**. Trois voies de
contournement sont possibles : produit-bundle nommé (recommandé), plusieurs
lignes dans le devis, ou assistant **Ajouter option** après souscription.

### 11.2 Génération mensuelle automatique — livrée avec limitations

La tâche quotidienne nocturne (03 h) qui génère les factures récurrentes
aux jours anniversaire est **livrée**. Elle est **désactivée par défaut**
et doit être activée après configuration du tenant (§10.8).

**Limitation actuelle** : la génération automatique de la **première
facture** à l'activation du contrat n'est pas encore opérationnelle sur
l'environnement de démonstration. En attendant le correctif, la première
facture est créée manuellement selon §10.6. Les factures récurrentes des
cycles suivants seront concernées par la même contrainte.

**Statut** : fonctionnalité livrée, correctif de compatibilité en cours.

### 11.3 Workflow de relances (dunning)

La politique de relance des factures impayées (paliers de rappels,
courriels, sms) est en cours de développement. En démo technique, cette
absence est visible dans la liste des tâches d'arrière-plan (deux tâches
apparaissent en échec après chaque activation de contrat) — à masquer
pour un public non technique.

![File d'attente des tâches — 2 tâches en échec](images/demo/29-queue-jobs-list.png)

### 11.4 Pas d'interface pour le calendrier des jours fériés

Aucune vue Odoo ne permet de lister ou modifier les jours fériés. Ils
sont déterminés automatiquement par le pays configuré dans la fiche
société (§5.3) et dans les paramètres du workflow impayés (§6.4).

### 11.5 Connexion Splynx en environnement de démonstration

Les serveurs Splynx configurés sur l'environnement de démonstration ne
pointent pas vers de vrais services Splynx — ils servent uniquement à
montrer la mécanique de la fiche serveur, le chiffrement des secrets et
la traçabilité de l'événement d'activation.

**Pour une démo client formelle** : configurer un vrai serveur Splynx de
bac à sable en amont, en collaboration avec l'équipe d'intégration.

### 11.6 Mise en page PDF de facture

Le modèle PDF actuel est fonctionnel mais sobre (police par défaut, pas
de logo, mise en page basique). Une personnalisation graphique via la
mise en page Odoo standard est possible ; une refonte est prévue avec la
gestion des avoirs.

### 11.7 Pas de portail client self-service

Les clients n'ont pas d'espace en ligne pour consulter leurs factures ou
signer leur contrat. Toute action passe par le back-office. La signature
manuscrite scannée requiert l'intervention du commercial (upload du
scan).

---

## 12. Dépannage

### 12.1 « Vous n'êtes pas autorisé à créer 'Devis' / 'Contrat' »

L'utilisateur n'a pas les bons groupes. Voir §8. Le minimum pour la
démo : **Ventes / Utilisateur**, **Facturation / Facturation**, **AXIA /
Commercial**, **AXIA — Billing Manager**.

### 12.2 « Ce devis a déjà généré un contrat CTR-XXX »

Un devis ne peut générer qu'un seul contrat actif. Passer par **Action →
Remettre en devis** puis annuler le contrat existant avant de confirmer
à nouveau.

### 12.3 Le contrat reste en Brouillon et ne passe pas À signer

Vérifier que l'option **Génère un contrat CLM** est cochée sur le
produit de la ligne du devis. Sinon, le contrat ne sera pas créé
automatiquement.

### 12.4 Le compte de facturation ne s'affiche pas après activation

La création du compte de facturation est faite en arrière-plan et peut
prendre quelques secondes. Rafraîchir la liste **AXIA — RBM → Comptes
de facturation**. Si le compte reste absent au bout de 30 secondes,
solliciter l'équipe d'intégration (le traitement d'arrière-plan est
peut-être suspendu).

### 12.5 Le PDF de facture ne s'ouvre pas

Solliciter l'équipe d'intégration — un composant serveur peut être
manquant ou hors service.

### 12.6 « Aucun journal trouvé pour la société X »

La société n'a pas de plan comptable installé. Aller dans
**Configuration → Sociétés → [Société]** puis cliquer sur **Configurer
la comptabilité**.

### 12.7 La position fiscale ne s'applique pas automatiquement sur le devis

- Vérifier que **Détecter automatiquement** est coché sur la position
  fiscale (§4.3)
- Vérifier que le pays de la position correspond au pays du contact
  client
- En dernier recours, sélectionner manuellement sur le devis (onglet
  **Autres informations**)

---

## Pour aller plus loin

- **Répétition à blanc** : la première fois qu'on présente le guide, il
  est recommandé de dérouler l'intégralité du parcours §3 à §10 en
  chronométrant pour se familiariser avec les enchaînements et les
  temps de chargement.
- **Personnalisation pour un prospect** : le nom du contact démo (Sophie
  MARTIN), l'adresse, les intitulés d'offres peuvent être adaptés au
  contexte du prospect avant la présentation. Voir le guide technique
  pour la procédure de ré-provisionnement.
- **Guide technique compagnon** :
  `demo-billing-contrat-refacturation-technique.md` regroupe les scripts
  de démonstration, les URLs directes utiles en favoris, les procédures
  de dépannage serveur et les points d'attention côté environnement.
