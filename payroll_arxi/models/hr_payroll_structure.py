from odoo import models, api, _


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    @api.model
    def _get_default_rule_ids(self):
        if 'hr_payroll_structure_mz_employee_union_salary' in self.get_external_id()['id']:
            # UNIONIZED WORKERS
            return [
                (0, 0, {
                    'category_id': self.env.ref('hr_payroll.BASIC').id,
                    'name': _('Base'),
                    'code': 'BASE',
                    'sequence': 101,
                    'condition_select': 'none',
                    'appears_on_payslip': True,
                    'amount_select': 'code',
                    'amount_python_compute': 'result = payslip.paid_amount',
                }),
                (0, 0, {
                    'category_id': self.env.ref('hr_payroll.GROSS').id,
                    'name': _('Gross'),
                    'code': 'GROSS',
                    'sequence': 102,
                    'condition_select': 'none',
                    'appears_on_payslip': True,
                    'amount_select': 'code',
                    'amount_python_compute': 'result = categories.BASIC + categories.ALW',
                }),
                (0, 0, {
                    'category_id': self.env.ref('hr_payroll.NET').id,
                    'name': _('Net'),
                    'code': 'NET',
                    'sequence': 103,
                    'condition_select': 'none',
                    'appears_on_payslip': True,
                    'amount_select': 'code',
                    'amount_python_compute': 'result = categories.BASIC + categories.ALW + categories.DED',
                }),
                (0, 0, {
                    'category_id': self.env.ref('hr_payroll.DED').id,
                    'name': _('IRPS'),
                    'code': 'IRPS',
                    'sequence': 104,
                    'condition_select': 'none',
                    'appears_on_payslip': True,
                    'amount_select': 'code',
                    'amount_python_compute': 'result = -compute_irps(categories, employee)',
                }),
                (0, 0, {
                    'category_id': self.env.ref('hr_payroll.DED').id,
                    'name': _('Social Security'),
                    'code': 'NISS',
                    'sequence': 105,
                    'condition_select': 'none',
                    'appears_on_payslip': True,
                    'amount_select': 'code',
                    'amount_python_compute': 'result = (-0.03 * categories.BASIC) if employee_id.subject_to_social_security else 0.0',
                }),
                (0, 0, {
                    'category_id': self.env.ref('hr_payroll.DED').id,
                    'name': _('Union'),
                    'code': 'UNION',
                    'sequence': 106,
                    'condition_select': 'none',
                    'appears_on_payslip': True,
                    'amount_select': 'code',
                    'amount_python_compute': 'result = -0.01 * categories.BASIC',
                })
            ]
        elif 'hr_payroll_structure_mz_employee_occasional_salary' in self.get_external_id()['id']:
            # OCCASIONAL WORKERS
            return [
                (0, 0, {
                    'category_id': self.env.ref('hr_payroll.BASIC').id,
                    'name': _('Base'),
                    'code': 'BASE',
                    'sequence': 201,
                    'condition_select': 'none',
                    'appears_on_payslip': True,
                    'amount_select': 'code',
                    'amount_python_compute': 'result = payslip.paid_amount',
                }),
                (0, 0, {
                    'category_id': self.env.ref('hr_payroll.GROSS').id,
                    'name': _('Gross'),
                    'code': 'GROSS',
                    'sequence': 202,
                    'condition_select': 'none',
                    'appears_on_payslip': True,
                    'amount_select': 'code',
                    'amount_python_compute': 'result = categories.BASIC + categories.ALW',
                }),
                (0, 0, {
                    'category_id': self.env.ref('hr_payroll.NET').id,
                    'name': _('Net'),
                    'code': 'NET',
                    'sequence': 203,
                    'condition_select': 'none',
                    'appears_on_payslip': True,
                    'amount_select': 'code',
                    'amount_python_compute': 'result = categories.BASIC + categories.ALW + categories.DED',
                }),
                (0, 0, {
                    'category_id': self.env.ref('hr_payroll.DED').id,
                    'name': _('IRPS'),
                    'code': 'IRPS',
                    'sequence': 204,
                    'condition_select': 'none',
                    'appears_on_payslip': True,
                    'amount_select': 'code',
                    'amount_python_compute': 'result = -0.2 * categories.BASIC',
                })
            ]
        return super(HrPayrollStructure, self)._get_default_rule_ids()
