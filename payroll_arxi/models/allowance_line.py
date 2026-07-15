from odoo import models, fields


class AllowanceLine(models.Model):
    _name = 'allowance.line'

    date = fields.Date()
    salary_structure_type_ids = fields.Many2many('hr.payroll.structure.type')
    food_allowance_value = fields.Float()
    transport_allowance_value = fields.Float()
    updated = fields.Boolean()

    def cron_update_allowances(self):
        if allowance_line_ids := self.search([('date', '=', fields.Date.today()), ('updated', '=', False)]):
            for allowance_line_id in allowance_line_ids:
                contract_ids = self.env['hr.contract'].search([('structure_type_id', 'in', allowance_line_id.salary_structure_type_ids.ids)])
                for contract_id in contract_ids:
                    contract_id.food_allowance = allowance_line_id.food_allowance_value
                    contract_id.transport_allowance = allowance_line_id.transport_allowance_value
                allowance_line_id.updated = True
