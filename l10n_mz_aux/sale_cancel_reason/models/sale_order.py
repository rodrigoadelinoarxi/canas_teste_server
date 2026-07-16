from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    reason = fields.Char(size=50, copy=False, readonly=True)

    def action_cancel_with_reason(self):
        self.ensure_one()
        if self.state == 'draft':
            raise ValidationError(_('You can not cancel a draft sale order. '
                                    'You should either edit or delete this record.'))
        action = self.env['ir.actions.act_window']._for_xml_id('sale_cancel_reason.sale_reason_wizard_action')
        action.update({'context': {'default_order_id': self.id}})
        return action

    def action_rewrite(self):
        action = self.action_cancel_with_reason()
        action.update({'context': {'default_order_id': self.id, 'default_is_rewrite': True}})
        return action
