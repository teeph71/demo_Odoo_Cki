"""
ORM migration script to sync `assigned_by` with `create_uid` for existing repair orders.

Run inside `odoo-bin shell -d <db>` so `env` is available:

    ./odoo-bin shell -d <db> < repair_order/scripts/sync_assigned_by_orm.py

This uses the ORM (no raw SQL) and prints a summary.
"""
if 'env' not in globals():
    raise SystemExit("Run inside `odoo-bin shell -d <db>` where `env` is provided.")

Repair = env['bike.repair.order']
domain = [('assigned_by', '=', False)]
recs = Repair.search(domain)
total = len(recs)
updated = 0
for rec in recs:
    try:
        if rec.create_uid:
            rec.assigned_by = rec.create_uid.id
            updated += 1
    except Exception as e:
        # continue on errors but report
        print(f"Failed for id={rec.id}: {e}")

env.cr.commit()
print(f"Completed migration: {updated}/{total} records updated (assigned_by <- create_uid)")
