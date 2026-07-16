from odoo import models, fields, api


class UpdateAllowancesWizard(models.Model):
    _name = 'update.allowances.wizard'

    update_date = fields.Date(default=fields.Date.today())
    salary_structure_type_ids = fields.Many2many('hr.payroll.structure.type')
    food_allowance = fields.Float()
    transport_allowance = fields.Float()

    def update_allowances(self):
        self.env['allowance.line'].create({
            'date'                     : self.update_date,
            'salary_structure_type_ids': self.salary_structure_type_ids,
            'food_allowance_value'     : self.food_allowance,
            'transport_allowance_value': self.transport_allowance,
        })
