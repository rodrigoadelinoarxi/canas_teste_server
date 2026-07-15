import base64
import datetime
import io
import logging

from odoo.tools.misc import xlwt
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class FilosoftExportWizard(models.TransientModel):
    _name = "filosoft.export.wizard"
    _description = "Filosoft Export Wizard"

    def _get_employee_domain(self):
        return [('id', 'in', self.env['hr.employee'].search([('is_machine', '=', False)]).ids)]

    date_from = fields.Date(default=datetime.date.today().replace(day=1, month=(datetime.date.today().month - 1) if datetime.date.today().month != 1 else 1))
    date_to = fields.Date(default=datetime.date.today().replace(day=1, month=datetime.date.today().month) - datetime.timedelta(days=1))
    specific_employee = fields.Boolean()
    employee_id = fields.Many2one('hr.employee', domain=lambda self: self._get_employee_domain())

    # VALIDATION THAT ONLY ALLOWS FULL MONTH INTERVALS (FIRST AND LAST DAYS)
    @api.onchange('date_from', 'date_to')
    def set_first_or_last_day_of_month(self):
        if self.date_from.day != 1:
            self.date_from = self.date_from.replace(day=1)
        if self.date_to.day != (self.date_to.replace(day=1, month=self.date_to.month + 1) - datetime.timedelta(days=1)).day:
            self.date_to = self.date_to.replace(day=(self.date_to.replace(day=1, month=self.date_to.month + 1) - datetime.timedelta(days=1)).day)

    def export_filosoft_listing(self):
        # IF FIRST DATE > LAST DATE, SWTICH AND CHANGE DAYS TO/FROM LAST/FIRST
        if self.date_from > self.date_to:
            date_aux = self.date_from
            self.date_from = self.date_to.replace(day=1)
            self.date_to = date_aux.replace(day=(date_aux.replace(day=1, month=date_aux.month + 1) - datetime.timedelta(days=1)).day)
        # TWO DIFFERENT MODELS, TWO DIFFERENT DOMAINS
        payroll_management_domain = []
        payroll_management_domain += [('date_start', '>=', self.date_from), ('date_start', '<=', self.date_to)]
        payroll_management_domain += [('employee_id', '=', self.employee_id.id)] if self.specific_employee and self.employee_id else []
        filtered_payroll_management_records = self.env['timesheet.payroll.management'].sudo().search(payroll_management_domain)
        analytic_lines_domain = []
        analytic_lines_domain += [('date', '>=', self.date_from), ('date', '<=', self.date_to)]
        analytic_lines_domain += [('employee_id', '=', self.employee_id.id)] if self.specific_employee and self.employee_id else []
        filtered_analytic_line_records = self.env['account.analytic.line'].sudo().search(analytic_lines_domain)
        # RECORD CREATION: TWO RECORDSETS THAT ARE COMBINED LATER ON
        # "TIPO DE FUNCIONÁRIO" ALWAYS ASSUMED TO BE "F". CHANGE HARDCODED VALUES IF ANYTHING CHANGES
        # GRANTS AND ABSENCES ARE CONSIDERED TO BE 1 FULL WORKDAY. IF CHANGED, CHANGE THE HARDCODED VALUES
        exportable_payroll_records = [
            {
                "Número do Funcionário": record.employee_id.employee_number.zfill(5),  # 00000
                "Tipo do Funcionário": "F",  # F/O
                "Abono / Falta": record.type_of_grant_absence.grant_absence.upper() if record.type_of_grant_absence.grant_absence else None,  # A/F
                "Cod. Abono / Falta": record.type_of_grant_absence.grant_absence_code.zfill(3) if record.type_of_grant_absence.grant_absence_code else None,  # 000
                "Quantidade": 1,  # 0000000000
                "Unidade": "DU",  # H/D/DU
                "Data Início": record.date_start.strftime("%d/%m/%Y"),  # DD/MM/AAAA
                "Data Fim": record.date_end.strftime("%d/%m/%Y")  # DD/MM/AAAA
            }
            for record in filtered_payroll_management_records if not record.employee_id.is_machine
        ]
        # UNITS CONSIDERED IN HOURS: CHANGE HARDCODED VALUE IF ANYTHING CHANGES
        exportable_analytic_line_records = [
            {
                "Número do Funcionário": record.employee_id.employee_number.zfill(5),  # 00000
                "Tipo do Funcionário": "F",  # F/O
                "Abono / Falta": None,  # A/F
                "Cod. Abono / Falta": None,  # 000
                "Quantidade": record.unit_amount,  # 0000000000
                "Unidade": "H",  # H/D/DU
                "Data Início": record.date.strftime("%d/%m/%Y"),  # DD/MM/AAAA
                "Data Fim": record.date.strftime("%d/%m/%Y")  # DD/MM/AAAA
            }
            for record in filtered_analytic_line_records if not record.employee_id.is_machine
        ]
        return self.print_xls_report(exportable_payroll_records + exportable_analytic_line_records)

    def print_xls_report(self, datas):
        # CREATES XLS FILE FROM DATASET: HEADERS ARE THE DICT KEYS, ROWS ARE THE VALUES. RETURNS A FILE DOWNLOAD ACTION
        workbook = xlwt.Workbook()
        sheet = workbook.add_sheet('filosoft_export_{}_{}.xls'.format(self.date_from.strftime("%d_%m_%Y"), self.date_to.strftime("%d_%m_%Y")))
        # HEADERS
        column = 0
        for key in datas[0]:
            sheet.write(0, column, key)
            column += 1
        # ROWS
        row = 1
        column = 0
        for data in datas:
            for key, value in data.items():
                sheet.write(row, column, value)
                column += 1
            row += 1
            column = 0
        # CREATE BINARY
        stream = io.BytesIO()
        workbook.save(stream)
        # CREATE ATTACHMENT
        attachment = {
            'name': 'filosoft_export_{}_{}.xls'.format(self.date_from.strftime("%d_%m_%Y"), self.date_to.strftime("%d_%m_%Y")),
            'datas': base64.encodebytes(stream.getvalue()),
            'datas_fname': 'filosoft_export_{}_{}.xls'.format(self.date_from.strftime("%d_%m_%Y"), self.date_to.strftime("%d_%m_%Y")),
            'res_model': 'filosoft.export.wizard',
            'type': 'binary'
        }
        attachment_id = self.env['ir.attachment'].sudo().create(attachment)
        # DOWNLOAD URL AND RETURN ACTION
        url = self.env['ir.config_parameter'].get_param('web.base.url') + '/web/content/' + str(attachment_id.id) + '?download=True'
        return {
            "type": "ir.actions.act_url",
            "url": url,
            "target": "new",
        }
