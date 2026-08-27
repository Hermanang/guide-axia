#!/usr/bin/env bash
# provision_demo_prod.sh
#
# Provisionne une DB Odoo fresh `axia_demo_prod` prête pour une démo
# client — currency EUR + plan comptable + tenant AXIA seul, sans la
# dette USD immuable de `axia_dev` (My Company créé en USD par défaut
# Odoo, immutable dès qu'il y a des journal items).
#
# Décision D4 review 2026-08-24 : la seule voie propre pour une démo
# client 100% EUR est une DB fresh avec CoA générique dès l'`-i`
# initial, PAS un contournement sur `axia_dev`.
#
# Usage :
#   ./docs/scripts/provision_demo_prod.sh [db_name]
#
# Par défaut db_name=axia_demo_prod. Durée estimée : 8-12 minutes selon
# machine (installation modules AXIA + l10n_generic_coa + fixtures).
#
# Après provisioning : lancer docs/scripts/setup_coqla_demo.py sur la
# nouvelle DB pour le tenant Coqla + 3 produits démo.

set -euo pipefail

DB="${1:-axia_demo_prod}"
DB_HOST="${DB_HOST:-postgres}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-odoo}"
DB_PASS="${DB_PASS:-odoo}"
ODOO_CONTAINER="${ODOO_CONTAINER:-deploy-odoo-1}"
PG_CONTAINER="${PG_CONTAINER:-deploy-postgres-1}"

echo "═══════════════════════════════════════════════════════════════"
echo " Provisionner DB fresh Odoo pour démo AXIA — $DB"
echo "═══════════════════════════════════════════════════════════════"

# 1. Vérifier que la DB n'existe pas déjà
if docker exec "$PG_CONTAINER" psql -U "$DB_USER" -lqt | cut -d\| -f1 | grep -qw "$DB"; then
    echo "[!] La DB '$DB' existe déjà."
    read -rp "    Écraser et recréer from scratch ? [y/N] " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo "    Annulé."; exit 1
    fi
    echo "[1] Drop DB existante..."
    docker exec "$PG_CONTAINER" dropdb -U "$DB_USER" "$DB"
fi

# 2. Créer DB vierge
echo "[2] Création DB vierge..."
docker exec "$PG_CONTAINER" createdb -U "$DB_USER" -O "$DB_USER" -E UTF8 -T template0 "$DB"

# 3. Init Odoo avec base + l10n_generic_coa + modules AXIA
echo "[3] Init Odoo + modules AXIA (~8-12 min)..."
docker exec "$ODOO_CONTAINER" odoo \
    -c /etc/odoo/odoo.conf \
    --db_host="$DB_HOST" --db_port="$DB_PORT" \
    --db_user="$DB_USER" --db_password="$DB_PASS" \
    -d "$DB" \
    -i base,l10n_generic_coa,axia_audit,axia_keychain,axia_rbac,axia_admin_params,axia_splynx_connector,axia_ppp,axia_credential_generator,axia_billing_workflow,axia_clm,axia_rbm \
    --stop-after-init --no-http --log-level=warn 2>&1 | tail -30

# 4. Configurer My Company en EUR + FR
echo "[4] Configurer société principale EUR + France (métropole)..."
docker exec "$ODOO_CONTAINER" python3 <<PYEOF
import xmlrpc.client
url = 'http://localhost:8069'
db = '$DB'
uid = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common').authenticate(db, 'admin', 'admin', {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# EUR + FR sur company 1
eur = models.execute_kw(db, uid, 'admin', 'res.currency', 'search', [[('name','=','EUR')]])[0]
fr = models.execute_kw(db, uid, 'admin', 'res.country', 'search', [[('code','=','FR')]])[0]
models.execute_kw(db, uid, 'admin', 'res.company', 'write', [[1], {
    'currency_id': eur, 'country_id': fr,
    'name': 'AXIA Démo (métropole)',
}])
print("  ✓ Company 1: EUR, FR, 'AXIA Démo (métropole)'")
PYEOF

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo " DB '$DB' prête. Étape suivante :"
echo ""
echo "   docker cp docs/scripts/setup_coqla_demo.py $ODOO_CONTAINER:/tmp/"
echo "   docker exec $ODOO_CONTAINER sh -c 'echo \"exec(open(\\\"/tmp/setup_coqla_demo.py\\\").read())\" | \\"
echo "     odoo shell -c /etc/odoo/odoo.conf --db_host=$DB_HOST --db_port=$DB_PORT \\"
echo "     --db_user=$DB_USER --db_password=$DB_PASS -d $DB --no-http --log-level=error'"
echo ""
echo " Puis pour tester le flow E2E : docs/scripts/test_coqla_e2e.py"
echo "═══════════════════════════════════════════════════════════════"
