from odoo import models, fields, api

class HrContractInherit(models.Model):
	_inherit = "hr.contract"
	_description = "hr.contract Inherit"

	structure_type_id_default = fields.Many2one('hr.payroll.structure.type', string="Salary Structure Type",  default=lambda self: self.env.ref('l10n_mz_hr_payroll.structure_type_employee_mz'))
	salary_structure = fields.Many2one('hr.payroll.structure')


