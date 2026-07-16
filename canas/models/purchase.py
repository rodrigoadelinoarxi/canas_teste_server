import json
import logging

from odoo import api, fields, models, _
from odoo.tools.misc import formatLang

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    has_equipment_code_lines = fields.Boolean(compute='_compute_has_equipment_code_lines', store=True)
    user_has_logistic_group = fields.Boolean(compute='_compute_user_has_groups')
    user_has_account_manager_group = fields.Boolean(compute='_compute_user_has_groups')
    work_project_id = fields.Many2one('project.project')

    pre_payment = fields.Boolean()
    is_import = fields.Boolean()
    equipment_code = fields.Many2one('equipment.code', related='order_line.equipment_code', string='Equipment')

    # TODO to remove after in master!
    x_studio__importao = fields.Boolean()
    x_studio_pr_pagamento = fields.Boolean()

    @api.depends('order_line', 'order_line.product_id')
    def _compute_has_equipment_code_lines(self):
        for order in self:
            order.has_equipment_code_lines = any(line.equipment_code for line in order.order_line)

    def _compute_user_has_groups(self):
        logistica_pt = self.env.user.has_group('canas.logistica_pt')
        group_account_manager = self.env.user.has_group('account.group_account_manager')
        for po in self:
            po.user_has_logistic_group = logistica_pt
            po.user_has_account_manager_group = group_account_manager

    @api.depends('order_line.price_total')
    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = amount_no_discount = amount_total_discount = 0.0
            for line in order.order_line:
                line._compute_amount()
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
                amount_no_discount += (line.product_qty * line.price_unit)
                amount_total_discount += ((line.product_qty * line.price_unit) - line.price_subtotal)
            currency = order.currency_id or order.partner_id.property_purchase_currency_id or self.env.company.currency_id
            order.update({
                'amount_untaxed': currency.round(amount_untaxed),
                'amount_tax': currency.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
                'amount_no_discount': currency.round(amount_no_discount),
                'amount_total_discount': currency.round(amount_total_discount),
            })

    @api.depends('order_line.taxes_id', 'order_line.price_subtotal', 'amount_total', 'amount_untaxed', 'order_line.first_discount', 'order_line.second_discount')
    def _compute_tax_totals_json(self):
        def compute_taxes(order_line):
            return order_line.taxes_id._origin.compute_all(**order_line._prepare_compute_all_values())

        account_move = self.env['account.move']
        for order in self:
            tax_lines_data = account_move._prepare_tax_lines_data_for_totals_from_object(order.order_line, compute_taxes)
            tax_totals = account_move._get_tax_totals(order.partner_id, tax_lines_data, order.amount_total, order.amount_untaxed, order.currency_id)
            # @ARXI
            tax_totals['discount'] = [{
                'name': _('Amount W/O Discount'),
                'amount': order.amount_no_discount,
                'formatted_amount': formatLang(self.env, order.amount_no_discount, currency_obj=order.currency_id),
            }, {
                'name': _('Total Discount'),
                'amount': order.amount_total_discount,
                'formatted_amount': formatLang(self.env, order.amount_total_discount, currency_obj=order.currency_id),
            }]
            # @ARXI
            order.tax_totals_json = json.dumps(tax_totals)

    amount_no_discount = fields.Monetary(
        string='Amount Without Discount',
        store=True,
        readonly=True,
        compute='_amount_all',
        tracking=True
    )
    amount_total_discount = fields.Monetary(
        string='Total Discount',
        store=True,
        readonly=True,
        compute='_amount_all',
        tracking=True
    )


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    equipment_code = fields.Many2one('equipment.code')
    equipment_code_required = fields.Boolean(
        related='product_id.product_tmpl_id.equipment_code_required',
        readonly=True
    )
    product_virtual_qty = fields.Float(
        'Available Product Quantity',
        related='product_id.virtual_available'
    )
    is_logistica_pt = fields.Boolean(related='order_id.user_has_logistic_group')
    is_request = fields.Boolean()

    # TODO to remove after in master!
    x_studio_pedido = fields.Boolean()
