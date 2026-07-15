from datetime import date

from odoo import models, fields, api, _
import logging

_logger = logging.getLogger(__name__)

class HrWorkEntry(models.Model):
    _inherit = 'hr.work.entry'

    unjustified_absence = fields.Boolean()
    unproductive = fields.Boolean()
    unsuccessful_maintenance = fields.Boolean()
    construction = fields.Many2one('project.project', compute='compute_construction', store=True)

    @api.depends('employee_id')
    def compute_construction(self):
        for rec in self:
            if rec.employee_id.contract_id.transfer_ids:
                for transfer in rec.employee_id.contract_id.transfer_ids:
                    if transfer.transfer_end_date:
                         if date(rec.date_start.year, rec.date_start.month, rec.date_start.day) >= transfer.transfer_start_date and date(rec.date_stop.year, rec.date_stop.month, rec.date_stop.day) <= transfer.transfer_end_date:
                            rec.construction = transfer.construction_id
                    elif date(rec.date_start.year, rec.date_start.month, rec.date_start.day) >= transfer.transfer_start_date:
                        rec.construction = transfer.construction_id
            else:
                analytic_account = rec.employee_id.contract_id.analytic_account_id
                project = self.env['project.project'].search([('analytic_account_id', '=', analytic_account.id)])
                rec.construction = project


    def action_view_work_entries(self):
        projects = self.env['project.project'].search([('construction_director', '=', self._uid)])
        analytic_accounts = []
        for project in projects:
            analytic_accounts.append(project.analytic_account_id.id)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Work Entry'),
            'res_model': 'hr.work.entry',
            'view_mode': 'gantt,calendar,list,pivot',
            'domain': [('construction.id', 'in', projects.ids)] if self.env.ref('hr_payroll.group_hr_payroll_manager') not in self.env.user.groups_id else False,
        }
