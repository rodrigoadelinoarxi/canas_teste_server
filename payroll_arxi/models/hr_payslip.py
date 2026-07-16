from odoo import models, fields, api, _
from odoo import Command
import logging
from odoo.tools.misc import format_date

from odoo.exceptions import UserError
from odoo.fields import Date
from odoo.tools import html2plaintext, date_utils
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class Payslip(models.Model):
    _inherit = 'hr.payslip'

    productivity_bonus_perc = fields.Float(string='Productivity Bonus', default=100)
    maintenance_bonus_perc = fields.Float(string='Maintenance Bonus', default=100)

    # date_from = fields.Date(
    #     string='From', readonly=True, required=True,
    #     default=lambda self: fields.Date.to_string(date.today().replace(day=21)),
    #     states={'draft': [('readonly', False)], 'verify': [('readonly', False)]})
    # date_to = fields.Date(
    #     string='To', readonly=True, required=True,
    #     default=lambda self: fields.Date.to_string((datetime.now() + relativedelta(months=+1, day=20)).date()),
    #     states={'draft': [('readonly', False)], 'verify': [('readonly', False)]})

    date_from = fields.Date(
        string='To', readonly=True, required=True,
        default=lambda self: fields.Date.to_string((datetime.now() + relativedelta(months=-1, day=21)).date()),
        states={'draft': [('readonly', False)], 'verify': [('readonly', False)]})

    date_to = fields.Date(
        string='From', readonly=True, required=True,
        default=lambda self: fields.Date.to_string(date.today().replace(day=20)),
        states={'draft': [('readonly', False)], 'verify': [('readonly', False)]})

    state = fields.Selection([
        ('draft', 'Draft'),
        ('validate', 'Engineer'),
        ('verify', 'Waiting'),
        ('done', 'Done'),
        ('paid', 'Paid'),
        ('cancel', 'Rejected')],
        string='Status', index=True, readonly=True, copy=False,
        default='draft', tracking=True,
        help="""* When the payslip is created the status is \'Draft\'
                    \n* If the payslip is under verification, the status is \'Waiting\'.
                    \n* If the payslip is confirmed then status is set to \'Done\'.
                    \n* When user cancel payslip the status is \'Rejected\'.""")

    bonus_warning = fields.Char(readonly=True, default=False)

    def calculate_payment_bonuses(self):
        for rec in self:
            payslip_input_lines = []
            payslip_input = self.env['hr.payslip.input']
            if rec.productivity_bonus_perc:
                input_type_productivity_bonus = self.env.ref('payroll_arxi.input_productivity_bonus')
                existing_input_line = rec.input_line_ids.filtered(
                    lambda line: line.input_type_id == input_type_productivity_bonus)
                if not existing_input_line:
                    payslip_input_lines.append(payslip_input.create({
                        'payslip_id': rec.id,
                        'input_type_id': input_type_productivity_bonus.id,
                        'name': 'Productivity Bonus',
                        'amount': rec.employee_id.contract_id.productivity_bonus * (rec.productivity_bonus_perc / 100),
                    }).id)

            if rec.maintenance_bonus_perc:
                input_type_maintenance_bonus = self.env.ref('payroll_arxi.input_maintenance_bonus')
                existing_input_line = rec.input_line_ids.filtered(
                    lambda line: line.input_type_id == input_type_maintenance_bonus)
                if not existing_input_line:
                    payslip_input_lines.append(payslip_input.create({
                        'payslip_id': rec.id,
                        'input_type_id': input_type_maintenance_bonus.id,
                        'name': 'Maintenance Bonus',
                        'amount': rec.employee_id.contract_id.maintenance_bonus * (rec.maintenance_bonus_perc / 100),
                    }).id)

            absences = self.env['hr.leave'].search([
                ('employee_ids', 'in', rec.employee_id.id),
                ('state', '=', 'validate'),
                ('holiday_status_id', '=', self.env.ref('payroll_arxi.unjustified_absence').id),
                ('request_date_from', '>=', rec.date_from),
                ('request_date_from', '<=', rec.date_to),
                '|', ('request_date_to', '>=', rec.date_from), ('request_date_from', '<=', rec.date_to)])

            if not absences:
                input_type_assiduity_bonus = self.env.ref('payroll_arxi.input_assiduity_bonus')
                existing_input_line = rec.input_line_ids.filtered(
                    lambda line: line.input_type_id == input_type_assiduity_bonus)
                if not existing_input_line:
                    payslip_input_lines.append(payslip_input.create({
                        'payslip_id': rec.id,
                        'input_type_id': input_type_assiduity_bonus.id,
                        'name': 'Assiduity Bonus',
                        'amount': rec.employee_id.contract_id.assiduity_bonus,
                    }).id)
            rec.input_line_ids = [(4, id) for id in payslip_input_lines]
            rec._compute_salary_attachment_ids()
            rec._compute_line_ids()
        self.state = 'validate'

    def compute_sheet(self):
        payslips = self.filtered(lambda slip: slip.state in ['draft', 'validate', 'verify'])
        # delete old payslip lines
        payslips.line_ids.unlink()
        # change the dates displayed in the batch
        payslip_run = self.env['hr.payslip.run'].search([('slip_ids', 'in', self.ids)])
        payslip_run.write({'date_start': (fields.Date.today() + relativedelta(months=-1)).replace(day=21), 'date_end': fields.Date.today().replace(day=20)})
        if len(payslips) > 1:
            for payslip in payslips.filtered(lambda slip: slip.state != 'cancel'):
                number = payslip.number or self.env['ir.sequence'].next_by_code('salary.slip')
                lines = [(0, 0, line) for line in payslip._get_payslip_lines()]
                payslip.write({'line_ids': lines, 'number': number, 'state': 'draft', 'date_from': (fields.Date.today() + relativedelta(months=-1)).replace(day=21), 'date_to': fields.Date.today().replace(day=20)})
        else:
            for payslip in payslips.filtered(lambda slip: slip.state != 'cancel'):
                number = payslip.number or self.env['ir.sequence'].next_by_code('salary.slip')
                lines = [(0, 0, line) for line in payslip._get_payslip_lines()]
                payslip.write({'line_ids': lines, 'number': number, 'state': 'verify', 'compute_date': fields.Date.today()})
        return True

    @api.model
    def _get_attachment_types(self):
        res = super(Payslip, self)._get_attachment_types()
        res.update({
            'advance': self.env.ref('payroll_arxi.input_advance'),
            'loan': self.env.ref('payroll_arxi.input_loan'),
            'cont_penalty': self.env.ref('payroll_arxi.input_contract_penalty'),
            'prem_reverse': self.env.ref('payroll_arxi.input_premium_reversal'),
            'jud_attach': self.env.ref('payroll_arxi.input_judicial_attachment'),
            'other_bonus': self.env.ref('payroll_arxi.input_other_bonus_attachment'),
            'retroactive': self.env.ref('payroll_arxi.input_retroactive_attachment'),
            'indemnity': self.env.ref('payroll_arxi.input_indemnity_attachment'),
            'vac_prop': self.env.ref('payroll_arxi.input_vac_prop_attachment'),
        })
        return res
    def _get_payslip_lines(self):
        self.ensure_one()

        localdict = self.env.context.get('force_payslip_localdict', None)
        if localdict is None:
            localdict = self._get_localdict()

        rules_dict = localdict['rules'].dict
        result_rules_dict = localdict['result_rules'].dict

        blacklisted_rule_ids = self.env.context.get('prevent_payslip_computation_line_ids', [])

        result = {}

        for rule in sorted(self.struct_id.rule_ids, key=lambda x: x.sequence):
            if rule.id in blacklisted_rule_ids:
                continue
            localdict.update({
                'result': None,
                'result_qty': 1.0,
                'result_rate': 100,
                'result_name': False
            })
            if rule._satisfy_condition(localdict):
                amount, qty, rate = rule._compute_rule(localdict)
                # check if there is already a rule computed with that code
                previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
                # set/overwrite the amount computed for this rule in the localdict
                tot_rule = amount * qty * rate / 100.0
                localdict[rule.code] = tot_rule
                result_rules_dict[rule.code] = {'total': tot_rule, 'amount': amount, 'quantity': qty}
                rules_dict[rule.code] = rule
                # sum the amount for its salary category
                localdict = rule.category_id._sum_salary_rule_category(localdict, tot_rule - previous_amount)
                # Retrieve the line name in the employee's lang
                employee_lang = self.employee_id.sudo().address_home_id.lang
                # This actually has an impact, don't remove this line
                context = {'lang': employee_lang}
                if localdict['result_name']:
                    rule_name = localdict['result_name']
                elif rule.code in ['BASIC', 'GROSS', 'NET', 'DEDUCTION',
                                   'REIMBURSEMENT']:  # Generated by default_get (no xmlid)
                    if rule.code == 'BASIC':  # Note: Crappy way to code this, but _(foo) is forbidden. Make a method in master to be overridden, using the structure code
                        if rule.name == "Double Holiday Pay":
                            rule_name = _("Double Holiday Pay")
                        if rule.struct_id.name == "CP200: Employees 13th Month":
                            rule_name = _("Prorated end-of-year bonus")
                        else:
                            rule_name = _('Basic Salary')
                    elif rule.code == "GROSS":
                        rule_name = _('Gross')
                    elif rule.code == "DEDUCTION":
                        rule_name = _('Deduction')
                    elif rule.code == "REIMBURSEMENT":
                        rule_name = _('Reimbursement')
                    elif rule.code == 'NET':
                        rule_name = _('Net Salary')
                else:
                    rule_name = rule.with_context(lang=self.env.user.lang).name
                # create/overwrite the rule in the temporary results
                result[rule.code] = {
                    'sequence': rule.sequence,
                    'code': rule.code,
                    'name': rule_name,
                    'note': html2plaintext(rule.note),
                    'salary_rule_id': rule.id,
                    'contract_id': localdict['contract'].id,
                    'employee_id': localdict['employee'].id,
                    'amount': amount,
                    'quantity': qty,
                    'rate': rate,
                    'slip_id': self.id,
                }
        return result.values()

    @api.onchange('date_from', 'date_to')
    def _compute_warning_message(self):
        today = Date.today()
        last_month = today + relativedelta(months=-1)

        for slip in self.filtered(lambda p: p.date_to):
            if (slip.date_from < last_month.replace(day=21)) or (slip.date_to > today.replace(day=20)):
                slip.warning_message = _(
                    "This payslip can be erroneous! "
                    "Work entries falling outside the range of %(start)s to %(end)s may not be processed.",
                    start=slip.date_from.strftime("%d/%m/%Y"),
                    end=slip.date_to.strftime("%d/%m/%Y"),
                )

            else:
                slip.warning_message = False

    @api.onchange('input_line_ids', 'input_line_ids.amount')
    def compute_bonus_warning(self):
        for rec in self:
            print("rec.contract_id.productivity_bonus: ", rec.contract_id.productivity_bonus)
            print("rec.contract_id.maintenance_bonus: ", rec.contract_id.maintenance_bonus)
            for line in rec.input_line_ids:
                print("line amount: ", line.amount)
                if line.input_type_id == rec.env.ref('payroll_arxi.input_productivity_bonus') and line.amount > rec.contract_id.productivity_bonus:
                    rec.bonus_warning = _('Productivity bonus amount is higher than the amount in the contract!')
                    return
                elif line.input_type_id == rec.env.ref('payroll_arxi.input_maintenance_bonus') and line.amount > rec.contract_id.maintenance_bonus:
                    rec.bonus_warning = _('Maintenance bonus amount is higher than the amount in the contract!')
                    return
                else:
                    rec.bonus_warning = False






    def vacations_days_left(self):
        a = self.env['hr.employee'].browse(self.employee_id.id)
        return int(a.allocation_count - a.allocation_used_count)

    def not_worked_days_method(self, worked_days):
        leave_work_entry_type = self.env['hr.work.entry.type'].browse(worked_days.work_entry_type_id.id)
        leave_without_pay = self.env['hr.work.entry'].search(
            [('employee_id', '=', self.employee_id.id), ('work_entry_type_id', '=', leave_work_entry_type.id),
             ('date_start', '>=', self.date_from), ('date_start', '<=', self.date_to)])
        leaves = self.env['hr.leave'].search([('employee_id', '=', self.employee_id.id),
                                              ('holiday_status_id.work_entry_type_id', '=', leave_work_entry_type.id),
                                              ('date_from', '>=', self.date_from), ('date_from', '<=', self.date_to)])
        not_worked_days = ''
        for rec in leaves:
            date_from = rec.date_from
            date_to = rec.date_to
            current_date = date_from

            while current_date <= date_to:
                not_worked_days += current_date.strftime("%d-%m-%Y") + ', '
                current_date += timedelta(days=1)
        return not_worked_days

    # def _get_worked_day_lines_values(self, domain=None):
    #     self.ensure_one()
    #     res = []
    #     hours_per_day = self._get_worked_day_lines_hours_per_day()
    #     leaves = self.env['hr.leave'].search(
    #         [('employee_id', '=', self.employee_id.id), ('date_from', '>=', self.date_from), ('date_from', '<=', self.date_to)])
    #     for leave in leaves:
    #         converted_date = datetime(self.date_to.year, self.date_to.month, self.date_to.day)
    #         number_of_days = leave.number_of_days
    #         if leave.date_to > converted_date:
    #             time_difference = (leave.date_to - converted_date).days
    #             number_of_days = number_of_days - time_difference
    #         entry_type = self.env['hr.work.entry.type'].browse(leave.holiday_status_id.work_entry_type_id.id)
    #         number_of_hours = leave.number_of_days * hours_per_day
    #         existing_entry = next((entry for entry in res if entry['work_entry_type_id'] == entry_type.id), None)
    #         if existing_entry:
    #             # Update existing entry
    #             existing_entry['number_of_days'] += number_of_days
    #             existing_entry['number_of_hours'] += number_of_hours
    #         else:
    #             # Add a new entry
    #             attendance_line = {
    #                 'sequence': entry_type.sequence,
    #                 'work_entry_type_id': entry_type.id,
    #                 'number_of_days': number_of_days,
    #                 'number_of_hours': number_of_hours,
    #             }
    #             res.append(attendance_line)
    #     work_hours = self.contract_id._get_work_hours(self.date_from, self.date_to, domain=domain)
    #     work_hours_ordered = sorted(work_hours.items(), key=lambda x: x[1])
    #     biggest_work = work_hours_ordered[-1][0] if work_hours_ordered else 0
    #     add_days_rounding = 0
    #     for work_entry_type_id, hours in work_hours_ordered:
    #         work_entry_type = self.env['hr.work.entry.type'].browse(work_entry_type_id)
    #         if work_entry_type.id == 1:
    #             days = round(hours / hours_per_day, 5) if hours_per_day else 0
    #             if work_entry_type_id == biggest_work:
    #                 days += add_days_rounding
    #             day_rounded = self._round_days(work_entry_type, days)
    #             day_rounded = round(day_rounded)
    #             hours = day_rounded * hours_per_day
    #             add_days_rounding += (days - day_rounded)
    #             attendance_line = {
    #                 'sequence': work_entry_type.sequence,
    #                 'work_entry_type_id': work_entry_type_id,
    #                 'number_of_days': day_rounded,
    #                 'number_of_hours': hours,
    #             }
    #             res.append(attendance_line)
    #     return res

    def _get_worked_day_lines_values(self, domain=None):
        res = super(Payslip, self)._get_worked_day_lines_values(domain)
        for line in res:
            _logger.warning('res: ' +str(line))
            line['number_of_days'] = round(line['number_of_days'])
        return res

    @api.depends('employee_id', 'contract_id', 'struct_id', 'date_from', 'date_to')
    def _compute_worked_days_line_ids(self):
        if self.env.context.get('salary_simulation'):
            return
        valid_slips = self.filtered(
            lambda p: p.employee_id and p.date_from and p.date_to and p.contract_id and p.struct_id)
        # Make sure to reset invalid payslip's worked days line
        invalid_slips = self - valid_slips
        invalid_slips.worked_days_line_ids = [(5, False, False)]
        # Ensure work entries are generated for all contracts
        generate_from = min(p.date_from for p in self)
        current_month_end = date_utils.end_of(fields.Date.today(), 'month')
        generate_to = max(min(fields.Date.to_date(p.date_to), current_month_end) for p in self)
        self.mapped('contract_id')._generate_work_entries(generate_from, generate_to)

        for slip in valid_slips:
            slip.write({'worked_days_line_ids': slip._get_new_worked_days_lines()})

    @api.depends('employee_id', 'struct_id', 'date_from')
    def _compute_name(self):
        for slip in self.filtered(lambda p: p.employee_id and p.date_from):
            lang = slip.employee_id.sudo().address_home_id.lang or self.env.user.lang
            context = {'lang': lang}
            payslip_name = slip.struct_id.payslip_name or _('Salary Slip')
            del context

            slip.name = '%(payslip_name)s - %(employee_name)s - %(dates)s' % {
                'payslip_name': payslip_name,
                'employee_name': slip.employee_id.name,
                'dates': format_date(self.env, slip.date_to, date_format="MMMM y", lang_code=lang)
            }
