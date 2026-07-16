import base64
import datetime
import logging
import time
from calendar import monthrange

import xlrd

from odoo import models, fields, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)

MOZ_ROWS = (0, 100)
EQUIP_ROWS = (101, 151)
PT_ROWS = (152, 166)
LAST_ROW = PT_ROWS[1] + 1


class ImportTimesheetLineWizard(models.TransientModel):
    _name = "import.timesheet.line.wizard"
    _description = "Import Timesheet Line Wizard"

    files = fields.Binary(string="Import Excel File")
    datas_fname = fields.Char(string="Import File Name")
    project_id = fields.Many2one('project.project')
    task_id = fields.Many2one('project.task')

    def timesheet_file(self):
        start_time = time.time()
        try:
            workbook = xlrd.open_workbook(file_contents=base64.b64decode(self.files), filename=self.datas_fname)
            sheet_name = workbook.sheet_names()
            sheet = workbook.sheet_by_name(sheet_name[0])
            date = datetime.datetime.date(xlrd.xldate.xldate_as_datetime(sheet.cell(6, 3).value, workbook.datemode))
            weekday, number_of_days = monthrange(date.year, date.month)
            days = [datetime.date(date.year, date.month, day) for day in range(1, number_of_days + 1)]
        except:
            raise ValidationError(_("Required formats are not being used. Please verify the Excel file and try again."))
        file_read_time = time.time()
        _logger.info("File read in %.2f seconds." % (file_read_time - start_time))

        dataset = []
        rows = [row for row in sheet.get_rows()][8:LAST_ROW]
        row_creation_time = time.time()
        _logger.info("Rows created in %.2f seconds." % (row_creation_time - file_read_time))

        if self.env.context.get('default_res_id') == 'project.task':
            active_id = self._context.get('active_id')
            task_id = self.env['project.task'].search([('id', '=', active_id)])
            project_id = task_id.project_id
            account_id = task_id.project_id.analytic_account_id
        else:
            project_id = self.project_id
            task_id = self.task_id
            account_id = task_id.project_id.analytic_account_id

        # COUNTER USED TO DISPLAY LINE INFORMATION
        row_number = 1
        mozambique_timesheet = True

        # START ROW ITERATION
        for row in rows:
            if row_number in range(*PT_ROWS):
                mozambique_timesheet = False
            row_number += 1
            # INDEX 0 -> employee_number / INDEX 1 -> name / INDEX 2 -> trash (ignore) / INDEX 3:END -> unit_amount
            # EMPTY ID AND NAME ASSUMES EMPTY LINE, THUS EMPTY DOCUMENT FROM THERE ON -> EXITS ITERATION
            # EMPTY ID AND NAME AND MOZAMBIQUE_TIMESHEET SWITCHES TO OVERSEAS TIMESHEET
            if not (row[0].value and row[1].value):
                continue
            search_domain = []
            number_or_code = None
            employee_id = False
            fleet_vehicle_id = False
            if row[0].value:
                number_or_code = int(row[0].value) if isinstance(row[0].value, float) else row[0].value
                search_domain += [('employee_number', '=', number_or_code), ('is_machine', '=', False)]
                employee_id = self.env['hr.employee'].sudo().search(search_domain, limit=1)
            if not employee_id:
                equipment_code = self.env['equipment.code'].search([('name', '=', number_or_code)], limit=1)
                if equipment_code:
                    employee_id = self.env['hr.employee'].sudo().search([('is_machine', '=', True), ('employee_number', '=', number_or_code)], limit=1)
                    fleet_vehicle_id = equipment_code.equipment_id.id
                else:
                    raise ValidationError(_(
                        "No employee or machine found for row #{}: please make sure that either the ID field or name are correct!"
                    ).format(row_number + 7))
            # START COLUMN ITERATION (INDEX 3 -> TIME DATA)
            day_index = 3
            today = datetime.datetime.today().date()
            for day in days:
                row_value = row[day_index].value
                if not row_value or (isinstance(row_value, str) and not row_value.strip()):
                    day_index += 1
                    continue
                create_timesheet_record = False
                hours_worked = 0.0
                origin = _("Mozambique") if not mozambique_timesheet else _("Overseas")
                destination = _("Mozambique") if mozambique_timesheet else _("Overseas")
                description = _("{}: {}H - Timesheet batch import done on {}").format(destination, row_value, today)
                type_of_grant_absence = ''
                if isinstance(row_value, float):
                    if row_value > 24.0 or row_value < 0.0:
                        raise ValidationError(_(
                            "Invalid time in row #{}: please make sure that all time records are correct!"
                        ).format(row_number + 9))
                    else:
                        hours_worked = row_value
                        create_timesheet_record = True

                elif isinstance(row_value, str):
                    if row[day_index].value.lower() == 'v':
                        hours_worked = 24.0
                        description = _("Business trip: {} -> {}").format(origin, destination)
                        create_timesheet_record = True
                    elif row[day_index].value.lower() == 'nt':
                        hours_worked = 0.0
                        description = _("Did not work on this project")
                        create_timesheet_record = True
                    # elif row[day_index].value.lower() == 'f':
                    #     create_payroll_management_record = True
                    #     type_of_grant_absence = 'holiday'
                    # elif row[day_index].value.lower() == 'fj':
                    #     create_payroll_management_record = True
                    #     type_of_grant_absence = 'excused_absence'
                    # elif row[day_index].value.lower() == 'fi':
                    #     create_payroll_management_record = True
                    #     type_of_grant_absence = 'unexcused_absence'
                    else:
                        raise ValidationError(_(
                            "Invalid value in row #{} ({}): please make sure that all records are correct!"
                        ).format(row_number + 9, row_value))
                # CREATE RECORD
                if create_timesheet_record:
                    record = {
                        'company_id': self.env.company.id,
                        'project_id': project_id.id,
                        'task_id': task_id.id,
                        'account_id': account_id.id,
                        'date': day,
                        'employee_id': employee_id.id,
                        'name': description,
                        'unit_amount': hours_worked,
                        'fleet_vehicle_id': fleet_vehicle_id,
                        'tag_ids': [(4, self.env.ref(
                            'import_export_timesheets.mozambique_tag' if mozambique_timesheet
                            else 'import_export_timesheets.overseas_tag').id)]
                    }
                    # ADD RECORD TO DATASET
                    dataset.append(record)
                # INCREMENT INDEX TO ITERATE OVER TIME DATA CELLS
                day_index += 1
        try:
            if dataset:
                self.env['account.analytic.line'].sudo().create(dataset)
            dataset_creation_time = time.time()
            _logger.info("Dataset created in %.2f seconds." % (dataset_creation_time - row_creation_time))
            _logger.info(
                _(("Timesheet Line Import finished successfully in {}s: created {} account analytic line" + 's'
                    if len(dataset) > 1 else '')).format("%.2f" % (time.time() - start_time), len(dataset))
            )
        except Exception as e:
            _logger.error(e)
            raise ValidationError(_("Error while creating account analytic lines!"))
