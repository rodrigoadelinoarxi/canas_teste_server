import logging

from odoo import api, models, fields
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class Partner(models.Model):
    _inherit = "res.partner"

    business_name = fields.Char(index=True)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        res = super(Partner, self).name_search(name, args, operator, limit)
        args = args or []
        super_partner_ids = res and list(zip(*res))[0]
        domain = [('business_name', operator, name), ('id', 'not in', super_partner_ids)]
        partner_ids = self._search(expression.AND([domain, args]), limit=limit)
        res += self.browse(partner_ids).name_get()
        return res
