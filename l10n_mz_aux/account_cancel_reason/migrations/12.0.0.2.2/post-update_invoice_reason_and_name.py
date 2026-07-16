import odoo
from odoo import api, _, SUPERUSER_ID


def migrate(cr, version):
    cr.execute("""
        UPDATE account_invoice SET reason = LEFT(name, 50) WHERE type = 'out_refund' AND reason = 'Document Creation'
    """)
    cr.execute("""
        UPDATE account_invoice SET name = '' WHERE type = 'out_refund' AND reason = name
    """)
