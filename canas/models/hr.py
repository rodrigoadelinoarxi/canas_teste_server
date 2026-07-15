import logging

from odoo import api, fields, models
from odoo.osv import expression

_logger = logging.getLogger(__name__)


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    def _compute_default_tax_ids(self):
        tax_ids = self.env['account.tax'].search([('amount', '=', 17.0), ('type_tax_use', '=', 'purchase')], limit=1)
        return tax_ids.ids if tax_ids else []

    tax_ids = fields.Many2many(default=lambda self: self._compute_default_tax_ids())


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    company_vehicle = fields.Many2one('fleet.vehicle')
    is_expense_approver = fields.Boolean('Expense Approver')

    @api.model
    def _compute_expense_approval_employee_domain(self):
        for rec in self:
            return [('company_id', '=', rec.company_id.id), ('id', '!=', rec.id)]

    expense_approval_employee_ids = fields.Many2many(
        'hr.employee', 'expense_approval_rel', 'approval_supervisor', 'employee_id', string='Expense Approvals',
        domain=_compute_expense_approval_employee_domain,
        help='List of employees whose expense approvals are done by this employee'
    )

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = ['|', ('name', operator, name), ('employee_number', operator, name)]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)
