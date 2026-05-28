"""
Lightweight migration script to sync `assigned_by` with `create_uid`.

Usage (run inside your Odoo checkout):

    ./odoo-bin shell -d <db> < repair_order/scripts/sync_assigned_by.py

This script expects to run inside `odoo-bin shell` where the `env` variable is provided.
It updates rows where `assigned_by` is NULL to match `create_uid`.
"""

if 'env' not in globals():
    raise SystemExit("This script must be run inside `odoo-bin shell -d <db>` where `env` is available.")

# Direct SQL update is fast and safe for this simple migration
env.cr.execute(
    """
    UPDATE bike_repair_order
    SET assigned_by = create_uid
    WHERE assigned_by IS NULL
    """
)
env.cr.commit()

print("Migration complete: assigned_by synced from create_uid for bike_repair_order")
