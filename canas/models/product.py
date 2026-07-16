from odoo import fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_fuel_expense = fields.Boolean('Is Fuel Expense')
