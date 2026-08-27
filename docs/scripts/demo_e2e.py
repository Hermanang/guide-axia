"""Test E2E flow démo billing/contrat/refacturation."""
import logging
from datetime import date

_log = logging.getLogger("DEMO_E2E")
_log.setLevel(logging.INFO)


def run(env):
    print("\n" + "=" * 70)
    print("DEMO E2E — Billing/Contrat/Refacturation AXIA ISP")
    print("=" * 70)

    # Contexte
    admin = env.ref("base.user_admin")
    company = env["res.company"].browse(1)  # My Company GP
    env = env(user=admin.id, context=dict(env.context, allowed_company_ids=[company.id]))
    print(f"\n[SETUP] Company={company.name} (country={company.country_id.name})")
    print(f"[SETUP] User admin id={admin.id} groups_count={len(admin.groups_id)}")

    # 1. Ajouter admin au groupe commercial + billing manager (démo)
    g_commercial = env.ref("axia_rbac.group_axia_commercial")
    g_billing = env.ref("axia_rbm.group_axia_billing_manager", raise_if_not_found=False)
    g_sales = env.ref("sales_team.group_sale_manager")
    g_account = env.ref("account.group_account_invoice", raise_if_not_found=False)
    to_add = []
    for g in [g_commercial, g_billing, g_sales, g_account]:
        if g and g not in admin.groups_id:
            to_add.append(g.id)
    if to_add:
        admin.sudo().write({"groups_id": [(4, gid) for gid in to_add]})
        print(f"[SETUP] admin ajouté aux groupes: {to_add}")

    # 2. Créer/récupérer un customer
    partner_ref = "demo.customer.dupont"
    partner = env["res.partner"].search([("ref", "=", partner_ref)], limit=1)
    if not partner:
        partner = env["res.partner"].create({
            "name": "Jean DUPONT (démo)",
            "ref": partner_ref,
            "email": "jean.dupont@demo.axia.fr",
            "phone": "+590690123456",
            "street": "12 rue de la Démo",
            "city": "Pointe-à-Pitre",
            "zip": "97110",
            "country_id": env.ref("base.gp").id,
            "customer_rank": 1,
        })
        print(f"[SETUP] Partner créé id={partner.id} name={partner.name}")
    else:
        print(f"[SETUP] Partner réutilisé id={partner.id}")

    # 3. Le produit test (déjà en DB, id=56)
    product = env["product.template"].browse(56)
    print(f"[SETUP] Product template id={product.id} name={product.name} "
          f"is_contract={product.is_contract} list_price={product.list_price}")
    if not product.product_variant_id:
        raise RuntimeError("Product template sans variant")
    variant = product.product_variant_id

    # 4. Créer devis
    print("\n" + "-" * 70)
    print("[ETAPE 1] Créer devis sale.order")
    print("-" * 70)
    order = env["sale.order"].create({
        "partner_id": partner.id,
        "company_id": company.id,
        "order_line": [(0, 0, {
            "product_id": variant.id,
            "product_uom_qty": 1.0,
        })],
    })
    print(f"  → Devis créé id={order.id} name={order.name} state={order.state} "
          f"amount_total={order.amount_total}")

    # 5. Confirmer le devis
    print("\n" + "-" * 70)
    print("[ETAPE 2] Confirmer le devis (action_confirm)")
    print("-" * 70)
    try:
        order.action_confirm()
        print(f"  → Devis confirmé state={order.state}")
        order.invalidate_recordset()  # cache O2M
        contracts = order.axia_contract_ids
        print(f"  → axia_contract_ids count={len(contracts)}")
        if contracts:
            c = contracts[0]
            print(f"  → Contrat créé id={c.id} number={c.number} state={c.state} "
                  f"correlation_id={c.correlation_id_root[:12] if c.correlation_id_root else None}...")
    except Exception as e:
        print(f"  ✖ ECHEC action_confirm: {type(e).__name__}: {e}")
        raise

    # 6. Passage contrat draft → to_sign
    contract = contracts[0]
    print("\n" + "-" * 70)
    print("[ETAPE 3] Contrat: passage draft → to_sign")
    print("-" * 70)
    for act_name in ("action_to_sign", "action_send_to_sign", "action_generate_pdf"):
        if hasattr(contract, act_name):
            print(f"  → available: {act_name}")

    # Try action_to_sign
    if hasattr(contract, "action_to_sign"):
        try:
            contract.action_to_sign()
            print(f"  → Contrat passé to_sign state={contract.state}")
        except Exception as e:
            print(f"  ⚠ action_to_sign: {type(e).__name__}: {e}")

    # 7. Signer + activer
    print("\n" + "-" * 70)
    print("[ETAPE 4] Contrat: signature → active")
    print("-" * 70)
    print(f"  → State courant: {contract.state}")

    for act_name in ("action_sign", "action_sign_manual", "action_activate", "action_confirm"):
        if hasattr(contract, act_name):
            print(f"  → available: {act_name}")

    if hasattr(contract, "action_activate"):
        try:
            contract.action_activate()
            print(f"  → activated state={contract.state}")
        except Exception as e:
            print(f"  ⚠ action_activate: {type(e).__name__}: {e}")

    # 8. Vérifier billing_account créé (via handler queue_job)
    print("\n" + "-" * 70)
    print("[ETAPE 5] Vérifier axia.billing.account (dispatch queue_job)")
    print("-" * 70)
    # Exec queue jobs immédiatement (bypass async)
    Job = env["queue.job"].sudo()
    pending = Job.search([("state", "in", ("pending", "enqueued"))], limit=20)
    print(f"  → Jobs pending: {len(pending)}")
    for j in pending:
        print(f"    - {j.name} state={j.state} channel={j.channel}")
    # Exécuter les jobs synchronement pour la démo
    from odoo.addons.queue_job.job import Job as QJ
    for j in pending:
        try:
            job = QJ.load(env, j.uuid)
            job.perform()
            job.set_done("done by demo E2E")
            job.store()
            print(f"    ✓ Exec: {j.name}")
        except Exception as e:
            print(f"    ✖ Exec {j.name}: {type(e).__name__}: {e}")
    env.cr.commit()

    # Force re-fetch
    env.invalidate_all()
    billing = env["axia.billing.account"].search([("contract_id", "=", contract.id)], limit=1)
    if billing:
        print(f"  → BillingAccount id={billing.id} number={billing.number} "
              f"state={billing.state} contract_id={billing.contract_id}")
    else:
        print(f"  ⚠ BillingAccount non trouvé (dispatch async → jobs pending: {len(pending)})")

    # 9. Créer manuellement une facture récurrente Story 6.3
    if billing:
        print("\n" + "-" * 70)
        print("[ETAPE 6] Créer axia.invoice.recurring (première facture prorata)")
        print("-" * 70)
        # Fiscal position?
        Invoice = env["account.move"]
        vals = {
            "move_type": "out_invoice",
            "partner_id": partner.id,
            "company_id": company.id,
            "invoice_date": date(2026, 8, 22),
            "axia_billing_account_id": billing.id,
            "axia_period_start": date(2026, 8, 22),
            "axia_period_end": date(2026, 8, 31),
            "axia_cycle_index": 1,
            "axia_invoice_type": "first_cycle",
            "invoice_line_ids": [(0, 0, {
                "product_id": variant.id,
                "quantity": 1.0,
                "price_unit": round(product.list_price * 10 / 31, 2),
                "name": f"{product.name} — prorata 22-31/08/2026",
            })],
        }
        try:
            inv = Invoice.create(vals)
            print(f"  → Facture id={inv.id} state={inv.state} "
                  f"axia_invoice_type={inv.axia_invoice_type} "
                  f"amount_untaxed={inv.amount_untaxed} "
                  f"amount_total={inv.amount_total} "
                  f"tax_label={inv.axia_tax_label}")
            # try post
            try:
                inv.action_post()
                print(f"  → Facture postée name={inv.name} state={inv.state}")
            except Exception as e:
                print(f"  ⚠ action_post: {type(e).__name__}: {e}")
            # PDF report
            report = env.ref("axia_rbm.axia_invoice_recurring_report", raise_if_not_found=False)
            if report:
                try:
                    pdf, _ = report._render_qweb_pdf(report.report_name, res_ids=inv.ids)
                    print(f"  → PDF Story 6.3 généré ({len(pdf)} bytes)")
                except Exception as e:
                    print(f"  ⚠ PDF render: {type(e).__name__}: {e}")
            else:
                print(f"  ⚠ report axia_rbm.axia_invoice_recurring_report absent")
        except Exception as e:
            print(f"  ✖ create facture: {type(e).__name__}: {e}")
            raise

    # 10. Audit events
    print("\n" + "-" * 70)
    print("[ETAPE 7] Audit trail")
    print("-" * 70)
    corr = contract.correlation_id_root
    events = env["axia.audit.event"].search(
        [("correlation_id", "=", corr)],
        order="created_at asc",
    )
    print(f"  → {len(events)} événements audit pour correlation_id={corr[:12]}...")
    for e in events:
        print(f"    - {e.event_type} target={e.target_model}#{e.target_id}")

    # 11. Rapport final
    print("\n" + "=" * 70)
    print("RESULTAT FINAL")
    print("=" * 70)
    print(f"Devis:           {order.name} state={order.state}")
    print(f"Contrat:         {contract.number} state={contract.state}")
    if billing:
        print(f"Billing account: {billing.number} state={billing.state}")
    if billing and 'inv' in dir():
        pass
    env.cr.commit()
    return {"order": order.id, "contract": contract.id,
            "billing": billing.id if billing else None}


# Entry point
run(env)
