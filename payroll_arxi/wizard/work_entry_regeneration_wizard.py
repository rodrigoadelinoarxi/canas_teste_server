from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class HrWorkEntryRegenerationWizard(models.TransientModel):
    _inherit = 'hr.work.entry.regeneration.wizard'

    construction_id = fields.Many2one('project.project', required=True)
    employee_id = fields.Many2one('hr.employee', 'Employee', required=False)

    @api.depends('date_from', 'date_to', 'employee_id', 'construction_id')
    def _compute_search_criteria_completed(self):
        for wizard in self:
            wizard.search_criteria_completed = (
                                                       wizard.date_from and wizard.date_to and wizard.employee_id and wizard.earliest_available_date and wizard.latest_available_date) or (
                                                       wizard.date_from and wizard.date_to and wizard.construction_id)

    @api.depends('date_from', 'date_to', 'employee_id', 'construction_id')
    def _compute_validated_work_entry_ids(self):
        for wizard in self:
            validated_work_entry_ids = self.env['hr.work.entry']
            if wizard.search_criteria_completed:
                if self.employee_id:
                    search_domain = [('employee_id', '=', self.employee_id.id),
                                     ('date_start', '>=', self.date_from),
                                     ('date_stop', '<=', self.date_to),
                                     ('state', '=', 'validated')]
                    validated_work_entry_ids = self.env['hr.work.entry'].search(search_domain, order="date_start")
                else:
                    # EMPLOYEES IN THE CONSTRUCTION
                    employees = self.env['hr.employee'].search([('contract_id.state', '=', 'open'), '|', (
                        'contract_id.analytic_account_id', '=', self.construction_id.analytic_account_id.id), (
                                                                    'contract_id.transfer_ids.construction_id.analytic_account_id',
                                                                    '=', self.construction_id.analytic_account_id.id)])
                    if employees:
                        for e in employees:
                            # Compute default entries
                            if e.contract_id.analytic_account_id == self.construction_id.analytic_account_id:
                                search_domain = [('employee_id', '=', e.id),
                                                 ('date_start', '>=', self.date_from),
                                                 ('date_stop', '<=', self.date_to),
                                                 ('state', '=', 'validated')]
                                validated_work_entry_ids = self.env['hr.work.entry'].search(search_domain,
                                                                                            order="date_start")
                            # HAS TRANSFERS
                            if e.contract_id.transfer_ids:
                                for transfer in e.contract_id.transfer_ids:
                                    # TRANSFER TO SELECTED CONSTRUCTION
                                    if transfer.construction_id == self.construction_id:
                                        search_domain = [('employee_id', '=', e.id),
                                                         ('date_start', '>=', transfer.transfer_start_date),
                                                         ('date_stop', '<=', transfer.transfer_end_date),
                                                         ('state', '=', 'validated')]
                                        validated_work_entry_ids = self.env['hr.work.entry'].search(search_domain,
                                                                                                    order="date_start")
                            # NO TRANSFERS
                            else:
                                search_domain = [('employee_id', '=', e.id),
                                                 ('date_start', '>=', self.date_from),
                                                 ('date_stop', '<=', self.date_to),
                                                 ('state', '=', 'validated')]
                                validated_work_entry_ids = self.env['hr.work.entry'].search(search_domain,
                                                                                            order="date_start")
            wizard.validated_work_entry_ids = validated_work_entry_ids

    def regenerate_work_entries(self):
        self.ensure_one()
        if not self.env.context.get('work_entry_skip_validation'):
            if not self.valid:
                raise ValidationError(
                    _("In order to regenerate the work entries, you need to provide the wizard with an employee_id, a date_from and a date_to. In addition to that, the time interval defined by date_from and date_to must not contain any validated work entries."))
            if self.earliest_available_date and self.latest_available_date:
                if self.date_from < self.earliest_available_date or self.date_to > self.latest_available_date:
                    raise ValidationError(
                        _("The from date must be >= '%(earliest_available_date)s' and the to date must be <= '%(latest_available_date)s', which correspond to the generated work entries time interval.",
                          earliest_available_date=self._date_to_string(self.earliest_available_date),
                          latest_available_date=self._date_to_string(self.latest_available_date)))

        date_from = max(self.date_from,
                        self.earliest_available_date) if self.earliest_available_date else self.date_from
        date_to = min(self.date_to, self.latest_available_date) if self.latest_available_date else self.date_to
        if self.employee_id:
            # Check employee construction
            if (
                    self.employee_id.contract_id.analytic_account_id.id == self.construction_id.analytic_account_id.id
                    or any(transfer.construction_id == self.construction_id for transfer in
                           self.employee_id.contract_id.transfer_ids)
            ):
                work_entries = self.env['hr.work.entry'].search([
                    ('employee_id', '=', self.employee_id.id),
                    ('date_stop', '>=', date_from),
                    ('date_start', '<=', date_to),
                    ('state', '!=', 'validated')])
                work_entries.write({'active': False})
                self.employee_id.generate_work_entries(date_from, date_to, True)
            else:
                raise ValidationError(_('This user is not allocated to that Construction'))
        else:
            # EMPLOYEES IN THE CONSTRUCTION
            employees = self.env['hr.employee'].search([('contract_id.state', '=', 'open'), '|', (
                'contract_id.analytic_account_id', '=', self.construction_id.analytic_account_id.id), (
                                                            'contract_id.transfer_ids.construction_id.analytic_account_id',
                                                            '=', self.construction_id.analytic_account_id.id)])
            if employees:
                for e in employees:
                    # HAS TRANSFERS
                    if e.contract_id.transfer_ids:
                        for transfer in e.contract_id.transfer_ids:
                            # TRANSFER TO SELECTED CONSTRUCTION
                            if transfer.construction_id == self.construction_id:
                                date_from_transfer = transfer.transfer_start_date if transfer.transfer_start_date else date_from
                                date_to_transfer = transfer.transfer_end_date if transfer.transfer_end_date else date_to
                                work_entries = self.env['hr.work.entry'].search([
                                    ('employee_id', '=', e.id),
                                    ('date_stop', '>=', date_from_transfer),
                                    ('date_start', '<=', date_to_transfer),
                                    ('state', '!=', 'validated')])
                                work_entries.write({'active': False})
                                e.generate_work_entries(date_from_transfer, date_to_transfer, True)
                            else:
                                date_from_transfer = transfer.transfer_start_date if transfer.transfer_start_date else date_from
                                date_to_transfer = transfer.transfer_end_date if transfer.transfer_end_date else date_to

                                search_domain = [('employee_id', '=', e.id),
                                                 ('date_start', '>=', date_from_transfer),
                                                 ('date_stop', '<=', date_to_transfer),
                                                 ('state', '=', 'draft')]

                                work_entries_to_delete = self.env['hr.work.entry'].search(search_domain,
                                                                                          order="date_start")
                                for entry in work_entries_to_delete:
                                    entry.unlink()

                    # NO TRANSFERS
                    else:
                        work_entries = self.env['hr.work.entry'].search([
                            ('employee_id', '=', e.id),
                            ('date_stop', '>=', date_from),
                            ('date_start', '<=', date_to),
                            ('state', '!=', 'validated')])
                        work_entries.write({'active': False})
                        e.generate_work_entries(date_from, date_to, True)

        action = self.env["ir.actions.actions"]._for_xml_id('hr_work_entry.hr_work_entry_action')
        return action
