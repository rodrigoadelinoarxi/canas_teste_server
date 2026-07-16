from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SaleReasonWizard(models.TransientModel):
    _name = 'sale.reason.wizard'
    _description = "Sale Reason Wizard"

    reason = fields.Char(size=50, required=True)
    order_id = fields.Many2one('sale.order', readonly=1)
    is_rewrite = fields.Boolean(string='Is a Rewrite')

    def confirm(self):
        """
        Cancels the sale order, adds a reason and does a copy if it needs a rewrite
        """
        self.order_id.write({'reason': self.reason})
        self.order_id._action_cancel()
        if self.is_rewrite:
            order_copy = self.order_id.copy()
            order_copy.message_subscribe(self.order_id.message_partner_ids.ids)
            order_copy.write(self.add_info_to_copy())

            return {
                'type'     : 'ir.actions.act_window',
                'view_mode': 'form',
                'res_model': 'sale.order',
                'res_id'   : order_copy.id,
                'context'  : dict(self.env.context, form_view_initial_mode='edit'),
            }
        return True

    def add_info_to_copy(self):
        """
        Aditional info to be passed onto the new copy
        :return: dict with values
        """
        return {}
