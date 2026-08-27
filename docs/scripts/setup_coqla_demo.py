"""Setup Coqla pour démo : nettoyage + config tenant + 3 produits."""
from datetime import date


def run(env):
    print("\n" + "=" * 70)
    print("SETUP DEMO COQLA — Nettoyage + Provisionning")
    print("=" * 70)

    admin = env.ref("base.user_admin")
    coqla = env["res.company"].browse(20)
    mycompany = env["res.company"].browse(1)

    # ------------------------------------------------------------------
    # 1. NETTOYAGE — annuler contrats / devis / factures démo
    # ------------------------------------------------------------------
    print("\n[1] NETTOYAGE")

    # 1a. Annuler contrats démo (draft, to_sign, active) via SQL direct
    # (pour éviter la logique métier avec préavis/pénalité)
    env.cr.execute("""
        UPDATE axia_contract SET state='cancelled'
        WHERE state != 'cancelled';
    """)
    print(f"  → Contrats: {env.cr.rowcount} annulés en cascade")

    # 1b. Annuler les billing accounts
    env.cr.execute("""
        UPDATE axia_billing_account SET state='closed'
        WHERE state != 'closed';
    """)
    print(f"  → Billing accounts: {env.cr.rowcount} fermés")

    # 1c. Devis / commandes — cancel
    env.cr.execute("""
        UPDATE sale_order SET state='cancel'
        WHERE state IN ('draft','sent','sale');
    """)
    print(f"  → Devis/commandes: {env.cr.rowcount} annulés")

    # 1d. Factures AXIA — draft puis cancel, ou reset draft si posted
    Move = env["account.move"]
    axia_moves = Move.search([("axia_invoice_type", "!=", False)])
    for m in axia_moves:
        if m.state == "posted":
            m.button_draft()
        if m.state == "draft":
            m.button_cancel()
    print(f"  → Factures AXIA: {len(axia_moves)} annulées")

    env.cr.commit()

    # ------------------------------------------------------------------
    # 2. USER — admin doit être sur Coqla
    # ------------------------------------------------------------------
    print("\n[2] USER admin — accès Coqla + groupes")
    for xmlid in (
        "sales_team.group_sale_manager",
        "account.group_account_manager",
        "account.group_account_invoice",
        "account.group_account_user",
        "axia_rbac.group_axia_commercial",
        "axia_rbac.group_axia_system_admin",
        "axia_rbm.group_axia_billing_manager",
    ):
        g = env.ref(xmlid, raise_if_not_found=False)
        if g and g not in admin.groups_id:
            admin.sudo().write({"groups_id": [(4, g.id)]})
            print(f"  → +group {xmlid}")

    admin.sudo().write({
        "company_ids": [(4, coqla.id)],
        "company_id": coqla.id,
    })
    print(f"  → default_company=Coqla ({coqla.id})")

    env = env(user=admin.id, context=dict(env.context, allowed_company_ids=[coqla.id]))

    # ------------------------------------------------------------------
    # 3. TAXE TVA 8,5% (Saint-Martin/DOM-TOM)
    # ------------------------------------------------------------------
    print("\n[3] TAXE — TVA 8,5% Saint-Martin")
    tax = env["account.tax"].search([
        ("company_id", "=", coqla.id),
        ("amount", "=", 8.5),
        ("type_tax_use", "=", "sale"),
    ], limit=1)
    if not tax:
        tg = env["account.tax.group"].search([("company_id", "=", coqla.id)], limit=1)
        if not tg:
            tg = env["account.tax.group"].create({
                "name": "Taxes de vente Saint-Martin",
                "company_id": coqla.id,
            })
        tax = env["account.tax"].create({
            "name": "TVA 8,5% (Saint-Martin/DOM-TOM)",
            "amount": 8.5,
            "amount_type": "percent",
            "type_tax_use": "sale",
            "company_id": coqla.id,
            "tax_group_id": tg.id,
        })
        print(f"  → Créée id={tax.id}")
    else:
        print(f"  → Existante id={tax.id}")

    # ------------------------------------------------------------------
    # 4. POSITION FISCALE — Saint-Martin avec axia_tax_label
    # ------------------------------------------------------------------
    print("\n[4] POSITION FISCALE — Saint-Martin")
    fp = env["account.fiscal.position"].search([
        ("company_id", "=", coqla.id),
        ("name", "=", "Saint-Martin (DOM-TOM)"),
    ], limit=1)
    if not fp:
        fp = env["account.fiscal.position"].create({
            "name": "Saint-Martin (DOM-TOM)",
            "company_id": coqla.id,
            "auto_apply": True,
            "country_id": env.ref("base.mf").id,
            "axia_tax_label": "TVA 8,5 %",
        })
        print(f"  → Créée id={fp.id} axia_tax_label={fp.axia_tax_label}")
    else:
        print(f"  → Existante id={fp.id}")

    # D2 review 2026-08-24 — mapping tax_ids obligatoire.
    # Sans lignes de correspondance de taxes, une position fiscale n'a
    # aucun effet fonctionnel Odoo (elle sert juste de placeholder pour
    # `axia_tax_label`). Bonne pratique FAI multi-juridiction : catalogue
    # produit central = taxes métropole (source), chaque tenant DOM-TOM/
    # NC/SN mappe vers sa taxe locale via la position fiscale (appliquée
    # automatiquement par `auto_apply=True` selon `country_id` client).
    metropole_20 = env["account.tax"].search([
        ("company_id", "=", coqla.id),
        ("amount", "=", 20.0),
        ("type_tax_use", "=", "sale"),
        ("name", "ilike", "20% S"),
    ], limit=1)
    if metropole_20 and not env["account.fiscal.position.tax"].search([
        ("position_id", "=", fp.id),
        ("tax_src_id", "=", metropole_20.id),
    ]):
        env["account.fiscal.position.tax"].create({
            "position_id": fp.id,
            "tax_src_id": metropole_20.id,
            "tax_dest_id": tva85.id,
        })
        print(f"  → Ligne mapping ajoutée: "
              f"{metropole_20.name} → {tva85.name}")

    # ------------------------------------------------------------------
    # 5. PRODUITS DEMO (3 offres)
    # ------------------------------------------------------------------
    print("\n[5] PRODUITS — 3 offres démo Coqla")
    Product = env["product.template"]
    # Purge anciens produits démo Coqla
    old = Product.search([
        ("company_id", "=", coqla.id),
        ("is_contract", "=", True),
    ])
    old.write({"active": False})
    print(f"  → {len(old)} anciens produits archivés")

    offers = [
        {
            "name": "Fibre Coqla 100M — Engagement 12 mois",
            "list_price": 29.90,
            "commitment_duration_months": 12,
            "description_sale": "Fibre optique 100 Mbps symétrique. "
                                "Installation offerte. Engagement 12 mois.",
        },
        {
            "name": "Triple Play Coqla — Fibre 300M + TV 4K + Téléphonie illimitée",
            "list_price": 49.90,
            "commitment_duration_months": 24,
            "description_sale": "Offre convergente : Fibre 300 Mbps + Bouquet "
                                "TV 4K (120 chaînes) + Téléphonie illimitée "
                                "fixe et mobile France + Antilles. "
                                "Engagement 24 mois.",
        },
        {
            "name": "Fibre Coqla 1 Gb Pro — Sans engagement",
            "list_price": 79.90,
            "commitment_duration_months": 0,
            "description_sale": "Fibre 1 Gbps pro. IP fixe incluse. "
                                "Support prioritaire 7j/7. Sans engagement.",
        },
    ]
    created_ids = []
    for spec in offers:
        p = Product.create({
            **spec,
            "type": "service",
            "is_contract": True,
            "company_id": coqla.id,
            "taxes_id": [(6, 0, [tax.id])],
            "invoice_policy": "order",
        })
        created_ids.append(p.id)
        print(f"  → id={p.id} {p.name} · {p.list_price:.2f} EUR · "
              f"engagement={p.commitment_duration_months}m")

    # ------------------------------------------------------------------
    # 6. CONFIG TENANT — quelques valeurs par défaut visibles
    # ------------------------------------------------------------------
    print("\n[6] CONFIG TENANT Coqla — valeurs de démo")
    tenant_vals = {}
    # CLM signature / paiement / résiliation
    if hasattr(coqla, "axia_signature_provider"):
        tenant_vals["axia_signature_provider"] = "manual_scan"
    if hasattr(coqla, "axia_default_payment_method"):
        tenant_vals["axia_default_payment_method"] = "sepa"
    if hasattr(coqla, "axia_termination_notice_period_days"):
        tenant_vals["axia_termination_notice_period_days"] = 30
    if hasattr(coqla, "axia_termination_penalty_policy"):
        tenant_vals["axia_termination_penalty_policy"] = "chatel_capped_25pct"
    if hasattr(coqla, "axia_termination_calendar_country"):
        tenant_vals["axia_termination_calendar_country"] = "FR"
    if hasattr(coqla, "axia_legitimate_motive_policy"):
        tenant_vals["axia_legitimate_motive_policy"] = "enabled"
    # Workflow impayés (axia_admin_params)
    if hasattr(coqla, "axia_suspension_enabled"):
        tenant_vals["axia_suspension_enabled"] = True
    if hasattr(coqla, "axia_suspension_mode"):
        tenant_vals["axia_suspension_mode"] = "delayed"
    if hasattr(coqla, "axia_suspension_delay_value"):
        tenant_vals["axia_suspension_delay_value"] = 15
    if hasattr(coqla, "axia_suspension_delay_unit"):
        tenant_vals["axia_suspension_delay_unit"] = "day"
    if hasattr(coqla, "axia_allow_grace_period"):
        tenant_vals["axia_allow_grace_period"] = True

    if tenant_vals:
        coqla.sudo().write(tenant_vals)
        print(f"  → {len(tenant_vals)} champs tenant configurés")
        for k, v in tenant_vals.items():
            print(f"    · {k} = {v}")

    env.cr.commit()

    # ------------------------------------------------------------------
    # 7. Bilan
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("BILAN COQLA DEMO")
    print("=" * 70)
    print(f"Currency:        {coqla.currency_id.name}")
    print(f"Country:         {coqla.country_id.name}")
    sale_journal = env["account.journal"].search(
        [("company_id", "=", coqla.id), ("type", "=", "sale")], limit=1)
    print(f"Sale journal:    {sale_journal.name} ({sale_journal.code})")
    print(f"Taxe TVA 8,5%:   id={tax.id}")
    print(f"Position fisc.:  id={fp.id} → axia_tax_label={fp.axia_tax_label}")
    print(f"Produits actifs: {len(created_ids)}")
    print(f"Contrats:        {env['axia.contract'].search_count([('state','!=','cancelled')])}")
    print(f"Devis actifs:    {env['sale.order'].search_count([('state','!=','cancel')])}")
    print(f"Fact. AXIA:      {env['account.move'].search_count([('axia_invoice_type','!=',False),('state','!=','cancel')])}")


run(env)
