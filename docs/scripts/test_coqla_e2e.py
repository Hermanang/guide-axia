"""Test E2E complet Coqla."""
from datetime import date


def run(env):
    admin = env.ref("base.user_admin")
    coqla = env["res.company"].browse(20)
    env = env(user=admin.id, context=dict(env.context, allowed_company_ids=[coqla.id]))

    # Client démo
    partner = env["res.partner"].create({
        "name": "Sophie MARTIN (démo Coqla)",
        "email": "sophie.martin@demo.coqla.sxm",
        "phone": "+590 590 40 00 00",
        "street": "8 boulevard de Grand-Case",
        "city": "Marigot",
        "zip": "97150",
        "country_id": env.ref("base.mf").id,
        "company_id": coqla.id,
        "customer_rank": 1,
    })
    print(f"[1] Client: {partner.name} id={partner.id}")

    # Devis avec Triple Play
    triple_play = env["product.template"].browse(292).product_variant_id
    order = env["sale.order"].create({
        "partner_id": partner.id,
        "company_id": coqla.id,
        "order_line": [(0, 0, {"product_id": triple_play.id, "product_uom_qty": 1.0})],
    })
    print(f"[2] Devis: {order.name} amount={order.amount_total} {order.currency_id.name}")

    # Confirm
    order.action_confirm()
    order.invalidate_recordset()
    contract = order.axia_contract_ids[0]
    print(f"[3] Contrat: {contract.number} state={contract.state}")

    # Activer
    if contract.state == "to_sign":
        contract.action_activate()
    print(f"[4] Contrat activé state={contract.state}")

    # Exec jobs
    from odoo.addons.queue_job.job import Job as QJ
    for j in env["queue.job"].sudo().search([("state", "in", ("pending", "enqueued"))]):
        try:
            job = QJ.load(env, j.uuid)
            job.perform()
            job.set_done("demo")
            job.store()
        except Exception:
            pass
    env.invalidate_all()

    billing = env["axia.billing.account"].search([("contract_id", "=", contract.id)], limit=1)
    print(f"[5] Billing account: {billing.number} state={billing.state}")

    # Facture prorata
    tax = env["account.tax"].browse(136)
    inv = env["account.move"].create({
        "move_type": "out_invoice",
        "partner_id": partner.id,
        "company_id": coqla.id,
        "invoice_date": date(2026, 8, 22),
        "fiscal_position_id": 32,
        "axia_billing_account_id": billing.id,
        "axia_period_start": date(2026, 8, 22),
        "axia_period_end": date(2026, 8, 31),
        "axia_cycle_index": 1,
        "axia_invoice_type": "first_cycle",
        "invoice_line_ids": [(0, 0, {
            "product_id": triple_play.id,
            "quantity": 1.0,
            "price_unit": round(49.90 * 10 / 31, 2),
            "name": "Triple Play Coqla — prorata 22-31/08/2026 (10 jours)",
            "tax_ids": [(6, 0, [tax.id])],
        })],
    })
    inv.action_post()
    print(f"[6] Facture: {inv.name} HT={inv.amount_untaxed} TTC={inv.amount_total} {inv.currency_id.name}")
    print(f"    tax_label={inv.axia_tax_label}")

    # PDF
    r = env.ref("axia_rbm.action_report_axia_invoice_recurring")
    pdf, _ = env["ir.actions.report"]._render_qweb_pdf(r.report_name, res_ids=inv.ids)
    with open("/tmp/facture_coqla_v2.pdf", "wb") as f:
        f.write(pdf)
    print(f"[7] PDF: {len(pdf)} bytes → /tmp/facture_coqla_v2.pdf")

    env.cr.commit()


run(env)
