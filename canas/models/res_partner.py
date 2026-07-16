from odoo import fields, models


class Partner(models.Model):
    _inherit = 'res.partner'

    fax = fields.Char(help="Fax Contact")
    supplier_code = fields.Char(string="Supplier Code")
