from odoo import models, api, _, fields


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    @api.model
    def _get_default_rule_ids(self):
        if self.get_external_id() and 'hr_payroll_structure_mz_employee_salary' in self.get_external_id().get('id'):
            return [
                (0, 0, {
                    'category_id': self.env.ref('hr_payroll.BASIC').id,
                    'name': _('Base'),
                    'code': 'BASE',
                    'sequence': 1,
                    'condition_select': 'none',
                    'appears_on_payslip': True,
                    'amount_select': 'code',
                    'amount_python_compute': 'result = payslip.paid_amount',
                }),
                (0, 0, {
                    'category_id': self.env.ref('hr_payroll.GROSS').id,
                    'name': _('Gross'),
                    'code': 'GROSS',
                    'sequence': 2,
                    'condition_select': 'none',
                    'appears_on_payslip': True,
                    'amount_select': 'code',
                    'amount_python_compute': 'result = categories.BASIC + categories.ALW',
                }),
                (0, 0, {
                    'category_id': self.env.ref('hr_payroll.NET').id,
                    'name': _('Net'),
                    'code': 'NET',
                    'sequence': 3,
                    'condition_select': 'none',
                    'appears_on_payslip': True,
                    'amount_select': 'code',
                    'amount_python_compute': 'result = categories.BASIC + categories.ALW + categories.DED',
                }),
                (0, 0, {
                    'category_id': self.env.ref('hr_payroll.DED').id,
                    'name': _('IRPS'),
                    'code': 'IRPS',
                    'sequence': 4,
                    'condition_select': 'none',
                    'appears_on_payslip': True,
                    'amount_select': 'code',
                    'amount_python_compute': 'result = -compute_irps(categories, employee)',
                }),
                (0, 0, {
                    'category_id': self.env.ref('hr_payroll.DED').id,
                    'name': _('Social Security'),
                    'code': 'NISS',
                    'sequence': 5,
                    'condition_select': 'none',
                    'appears_on_payslip': True,
                    'amount_select': 'code',
                    'amount_python_compute': 'result = (-0.03 * categories.BASIC) if employee_id.subject_to_social_security else 0.0',
                })
            ]
        return super(HrPayrollStructure, self)._get_default_rule_ids()

    rule_ids = fields.One2many('hr.salary.rule', 'struct_id', string='Salary Rules', default=_get_default_rule_ids)
