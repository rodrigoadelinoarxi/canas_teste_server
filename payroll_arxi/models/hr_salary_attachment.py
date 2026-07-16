from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _


class HrSalaryAttachment(models.Model):
    _inherit = 'hr.salary.attachment'

    number_of_days = fields.Float(string="Number of Days")

    deduction_type = fields.Selection(selection_add=[
        ('advance', 'Advance'),
        ('loan', 'Loan'),
        ('cont_penalty', 'Contract Penalty'),
        ('prem_reverse', 'Premium Reversal'),
        ('jud_attach', 'Judicial Attachment'),
        ('other_bonus', 'Other Bonus'),
        ('retroactive', 'Retroactive'),
        ('indemnity', 'Indemnity'),
        ('vac_prop', 'Vacation Proportion'),
    ], ondelete={
        'advance': lambda r: r.write({'type': 'attachment'}),
        'loan': lambda r: r.write({'type': 'attachment'}),
        'cont_penalty': lambda r: r.write({'type': 'attachment'}),
        'prem_reverse': lambda r: r.write({'type': 'attachment'}),
        'jud_attach': lambda r: r.write({'type': 'attachment'}),
        'other_bonus': lambda r: r.write({'type': 'attachment'}),
        'retroactive': lambda r: r.write({'type': 'attachment'}),
        'indemnity': lambda r: r.write({'type': 'attachment'}),
        'vac_prop': lambda r: r.write({'type': 'attachment'}),
    })

    deduction_type_select = fields.Selection([
        ('attachment', 'Attachment of Salary'),
        ('assignment', 'Assignment of Salary'),
        ('child_support', 'Child Support'),
        ('advance', 'Advance'),
        ('loan', 'Loan'),
        ('cont_penalty', 'Contract Penalty'),
        ('prem_reverse', 'Premium Reversal'),
        ('jud_attach', 'Judicial Attachment'),

    ], ondelete={
        'advance': lambda r: r.write({'type': 'attachment'}),
        'loan': lambda r: r.write({'type': 'attachment'}),
        'cont_penalty': lambda r: r.write({'type': 'attachment'}),
        'prem_reverse': lambda r: r.write({'type': 'attachment'}),
        'jud_attach': lambda r: r.write({'type': 'attachment'}),
    }, string='Type',
        required=True,
        default='attachment',
        tracking=True)

    addition_type = fields.Selection([
        ('other_bonus', 'Other Bonus'),
        ('retroactive', 'Retroactive'),
        ('indemnity', 'Indemnity'),
        ('vac_prop', 'Vacation Proportion'),
    ], ondelete={
        'other_bonus': lambda r: r.write({'type': 'attachment'}),
        'retroactive': lambda r: r.write({'type': 'attachment'}),
        'indemnity': lambda r: r.write({'type': 'attachment'}),
        'vac_prop': lambda r: r.write({'type': 'attachment'}),
    }, default='other_bonus'
    )

    @api.model
    def create(self, vals_list):
        if vals_list.get('addition_type'):
            if vals_list['addition_type'] == 'vac_prop':
                vals_list['monthly_amount'] = vals_list['number_of_days']
                days = vals_list['number_of_days']
                vacations = self.env['hr.leave'].search([('employee_id', '=', vals_list['employee_id']), (
                    'holiday_status_id', '=', self.env.ref('canas.vacation_status_paid').id),
                                                         ('request_date_from', '>', fields.date.today()),
                                                         ('state', '!=', 'refuse')], order="request_date_from asc")

                allocation = self.env['hr.leave.allocation'].search([('employee_id', '=', vals_list['employee_id']), (
                    'holiday_status_id', '=', self.env.ref('canas.vacation_status_paid').id),
                                                                     ])
                days_to_remove = days
                for vac in vacations:
                    previous_state = vac.state
                    vac.state = 'draft'
                    if days >= vac.number_of_days:
                        vac.state = 'refuse'
                        days -= vac.number_of_days
                    else:
                        i = 1
                        while i <= days:
                            request_date_from = vac.request_date_from + relativedelta(days=1)
                            if request_date_from.weekday() >= 6:
                                request_date_from = request_date_from + relativedelta(days=1)
                            i += 1
                            vac.update({
                                'request_date_from': request_date_from
                            })
                        days -= days
                        vac.state = previous_state
                    if days == 0:
                        break
                allocation.number_of_days -= days_to_remove
            vals_list['deduction_type'] = vals_list['addition_type']
            vals_list['total_amount'] = vals_list['monthly_amount']
        if vals_list.get('deduction_type_select'):
            vals_list['deduction_type'] = vals_list['deduction_type_select']
        res = super(HrSalaryAttachment, self).create(vals_list)
        return res

    def unlink(self):
        if self.addition_type == 'vac_prop':
            allocation = self.env['hr.leave.allocation'].search([('employee_id', '=', self.employee_id.id), (
                'holiday_status_id', '=', self.env.ref('canas.vacation_status_paid').id)])
            print("allocation: ", allocation.number_of_days)
            allocation.update({'number_of_days': allocation.number_of_days + self.number_of_days})
            print("allocation after: ", allocation.number_of_days)
        res = super().unlink()
        return res

    @api.onchange('addition_type')
    def _compute_description_addition(self):
        name = dict(self._fields['addition_type']._description_selection(self.env)).get(self.addition_type)
        self.description = name

    @api.onchange('deduction_type_select')
    def _compute_description_deduction(self):
        name = dict(self._fields['deduction_type_select']._description_selection(self.env)).get(
            self.deduction_type_select)
        self.description = name
