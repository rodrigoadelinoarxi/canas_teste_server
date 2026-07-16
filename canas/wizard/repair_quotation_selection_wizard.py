import logging
from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class RepairQuotationSelectionWizard(models.TransientModel):
    _name = 'repair.quotation.selection.wizard'
    _description = 'Repair Quotation Selection Wizard'

    repair_order_id = fields.Many2one('repair.order', 'Repair Order')
    state = fields.Selection([('parts', 'Parts'), ('operations', 'Operations')], default='parts')

    def get_operations_ids(self):
        repair_order_id = self.repair_order_id or self.env['repair.order'].browse(self.env.context['active_id'])
        return [(6, 0, repair_order_id.operations.ids)]

    def get_fees_lines_ids(self):
        repair_order_id = self.repair_order_id or self.env['repair.order'].browse(self.env.context['active_id'])
        return [(6, 0, repair_order_id.fees_lines.ids)]

    operations = fields.Many2many("repair.line", default=get_operations_ids)
    fees_lines = fields.Many2many("repair.fee", default=get_fees_lines_ids)

    def generate_purchase_order(self):
        view_id = self.env['purchase.order']
        purchase_order_line = self.env['purchase.order.line']
        new = view_id.create({
            'partner_id': self.env.user.id,
            'repair_id': self.repair_order_id.id
        })
        if self.state == 'operations':
            if not self.fees_lines:
                raise ValidationError(_("There are no operations for quotation creation!"))
            for line in self.fees_lines:
                purchase_qty = line.product_uom_qty
                new_line = purchase_order_line.create({
                    'product_id': line.product_id.id,
                    'name': line.product_id.name,
                    'date_planned': datetime.now() + relativedelta(days=+30),
                    'product_qty': purchase_qty,
                    'product_uom': line.product_id.uom_id.id,
                    'price_unit': line.price_unit,
                    'taxes_id': [(6, 0, line.product_id.supplier_taxes_id.ids)],
                    'order_id': new.id,
                })
                new.order_line = [(4, new_line.id)]
        else:
            if not self.operations:
                raise ValidationError(_("There are no parts for quotation creation!"))
            for line in self.operations:
                if line.product_uom_qty > line.product_available_qty:
                    purchase_qty = line.product_uom_qty if line.product_available_qty <= 0 else line.product_uom_qty - line.product_available_qty
                    new_line = purchase_order_line.create({
                        'product_id': line.product_id.id,
                        'name': line.product_id.name,
                        'date_planned': datetime.now() + relativedelta(days=+30),
                        'product_qty': purchase_qty,
                        'product_uom': line.product_id.uom_id.id,
                        'price_unit': line.price_unit,
                        'taxes_id': [(6, 0, line.product_id.supplier_taxes_id.ids)],
                        'order_id': new.id,
                    })
                    new.order_line = [(4, new_line.id)]
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Order',
            'view_mode': 'form',
            'view_id': self.env.ref('canas.purchase_order_form_view_override', False).id,
            'res_model': 'purchase.order',
            'res_id': new.id,
            'target': 'current'
        }
