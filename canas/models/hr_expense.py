from odoo import fields, models, api


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    is_fuel = fields.Boolean('Is Fuel')
    equipment_code = fields.Many2one('equipment.code')
    km_work_hours = fields.Char('Km/Work Hours')

    @api.onchange('product_id')
    def _set_expense_type(self):
        for expense in self:
            if expense.product_id and expense.product_id.is_fuel_expense:
                expense.is_fuel = True
