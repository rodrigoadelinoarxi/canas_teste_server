from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    no_negative_stock = fields.Boolean(string="Don't allow negative stocks", default=True)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    no_negative_stock = fields.Boolean(
        related='company_id.no_negative_stock',
        string="Don't allow negative stocks",
        readonly=False
    )
