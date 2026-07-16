from datetime import datetime, timedelta
from odoo import fields, models, api


import logging

_logger = logging.getLogger(__name__)


class Payslip(models.Model):
    _inherit = "hr.payslip"
    _description = "hr_payslip_inherit"

    structure = fields.Many2one('hr.payroll.structure', compute='onchange_employee_id', store=True)

    @api.depends('employee_id', 'contract_id.salary_structure')
    def onchange_employee_id(self):
        for rec in self:
            if rec.contract_id and rec.contract_id.state == 'open':
                rec.structure = rec.contract_id.salary_structure
                rec.struct_id = rec.structure
            else:
                rec.structure = False
                rec.struct_id = rec.structure
            if rec.struct_id:
                rec.structure = rec.struct_id

    def allowances_section_payslip(self):
        a = self.line_ids.filtered(lambda line: line.appears_on_payslip)
        allowances = []
        for rec in a:
            if rec.code == 'GROSS':
                break
            allowances.append(rec)
        return allowances

    def discount_section_payslip(self):
        a = self.line_ids.filtered(lambda line: line.appears_on_payslip)
        discounts = []
        for rec in a:
            if rec.sequence > 14 and rec.code != 'VL':
                discounts.append(rec)
        return discounts

    def get_not_worked_days_lines(self, worked_days_line_ids):
        worked_days_list = []
        for line in worked_days_line_ids.filtered(
                lambda w: w.code in ['SICK_LEAVE_NOT_PAID', 'LEAVE_WITHOUT_PAY', 'UNJUSTIFIED_ABSENCE',
                                     'MATERNITY_LEAVE', 'PARENTAL_LEAVE', 'PATERNITY_LEAVE']):
            if line.code not in [d["code"] for d in worked_days_list if d['code']]:
                worked_days_list.append({'code': line.code, 'name': line.name, 'amount': line.amount})
            else:
                if worked_days := list(filter(lambda d: d["code"] is line.code, worked_days_list)):
                    worked_days[0]["amount"] += line.amount
        return worked_days_list

    def get_not_worked_days_line_notes(self, worked_days_line_ids):
        worked_days_list = self.env['hr.payslip.worked_days']
        for line in worked_days_line_ids:
            _logger.info("line code: " +str(line.code))
            if line.code != self.env.ref('hr_work_entry.work_entry_type_attendance').code:
                worked_days_list += line
        return worked_days_list

    def not_worked_days_method(self, worked_days):
        days_list = ""
        days = super(Payslip, self).not_worked_days_method(worked_days).split(',')
        del days[-1]
        datas_list = [datetime.strptime(day.strip(), '%d-%m-%Y').date() for day in days]
        datas_list.sort()
        for date in datas_list:
            if worked_days[0].payslip_id.date_from <= date <= worked_days[0].payslip_id.date_to:
                days_list += f"{str(date.day)}/{str(date.month)}, "
        return days_list

    def _get_not_worked_days_number_of_days(self):
        wds = self.worked_days_line_ids.filtered(lambda wd: wd.code != self.env.ref('hr_work_entry.work_entry_type_attendance'))
        return sum([wd.number_of_days for wd in wds])
