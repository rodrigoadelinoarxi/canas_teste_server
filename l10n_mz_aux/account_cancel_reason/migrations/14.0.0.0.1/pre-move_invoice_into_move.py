import odoo
from odoo import api, _, SUPERUSER_ID


def migrate(cr, version):
    cr.execute("""ALTER TABLE account_move ADD COLUMN IF NOT EXISTS reason varchar""")
    cr.execute(
        """UPDATE account_move set reason = ai.reason from account_invoice ai where ai.move_id = account_move.id""")
