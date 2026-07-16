import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class SupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    price_without_discount = fields.Float(digits='Product Price')
    first_discount = fields.Float('First Discount (%)')
    second_discount = fields.Float('Second Discount (%)')
    price = fields.Float(compute='_compute_price', store=True)

    _sql_constraints = [
        ('first_discount_check', 'CHECK (first_discount>=0 AND first_discount<=100)',
         'The discount must be between 0 and 100.'),
        ('second_discount_check', 'CHECK (second_discount>=0 AND second_discount<=100)',
         'The discount must be between 0 and 100.'),
    ]

    @api.depends('price_without_discount', 'first_discount', 'second_discount')
    def _compute_price(self):
        for seller in self:
            first_discount_amount = (seller.price_without_discount * seller.first_discount) / 100
            second_discount_amount = ((seller.price_without_discount - first_discount_amount) * seller.second_discount) / 100
            seller.price = (seller.price_without_discount - first_discount_amount) - second_discount_amount
        return True
