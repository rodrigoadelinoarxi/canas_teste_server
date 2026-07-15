import logging
import math
from datetime import datetime
from pytz import timezone, utc

from odoo import _, fields, models
from odoo.exceptions import ValidationError

try:
    import holidays
except ImportError:
    raise ImportError('This module needs holidays installed on your system. (pip3 install holidays)')

_logger = logging.getLogger(__name__)


class HolidayWizard(models.TransientModel):
    _name = 'holiday.wizard'
    _description = 'Wizard to get national holidays'

    calendar_id = fields.Many2one('resource.calendar')
    year = fields.Char(size=4, required=True, default=lambda self: fields.Date.today().year)

    def default_get(self, fields_list):
        res = super(HolidayWizard, self).default_get(fields_list)
        calendar = self.env['resource.calendar'].browse(self._context.get('active_id'))
        res.update({'calendar_id': calendar.id})
        return res

    def action_get_holidays(self):
        self.ensure_one()
        holiday_list = self.env['resource.calendar.leaves'].search([('resource_id', '=', False), ('company_id', '=', self.calendar_id.company_id.id)])
        if holiday_list:
            return True
        if not self.calendar_id:
            raise ValidationError(_('Resource not found.'))
        if not self.calendar_id.company_id.country_id:
            raise ValidationError(_('This company needs to have a country defined.'))
        if not 1900 <= int(self.year) <= 2100:
            raise ValidationError(_('Invalid year.'))
        try:
            code = self.calendar_id.company_id.country_id.code.upper()
            if code not in holidays.list_supported_countries():
                code = self.sudo().with_context(lang=False).calendar_id.company_id.country_id.name.replace(" ", "")
            holiday_country = holidays.CountryHoliday(code)
        except Exception as e:
            _logger.info(e.__str__())
            raise ValidationError(
                _("It wasn't possible to get holidays for the country: %s",
                  self.calendar_id.company_id.country_id.name))

        first_day = fields.Date.from_string("%s-%s-%s" % (self.year, 1, 1))
        last_day = fields.Date.from_string("%s-%s-%s" % (self.year, 12, 31))
        all_holiday_days = holiday_country[first_day: last_day]

        res = {holiday_country.get(day): day for day in all_holiday_days}

        if res:
            tz = timezone(self.calendar_id.tz)
            global_leaves = []
            for name, holiday_date in res.items():
                if self.calendar_id.global_leave_ids.filtered(lambda l: l.date_from.date() == holiday_date):
                    continue

                # We get a date format and need to convert that to a datetime on the local timezone.
                # We also need to convert that date to UTC, since Odoo saves the date in a UTC format in the database.
                date_from_with_local_tz = tz.localize(datetime.combine(holiday_date, datetime.min.time()))

                date_to_with_local_tz = tz.localize(datetime.combine(holiday_date, datetime.max.time()))

                date_from_as_utc = date_from_with_local_tz.astimezone(utc).replace(tzinfo=None)
                date_to_as_utc = date_to_with_local_tz.astimezone(utc).replace(tzinfo=None)

                global_leaves.append((0, 0, {
                    'name'       : name,
                    'date_from'  : date_from_as_utc,
                    'date_to'    : date_to_as_utc,
                    'resource_id': False,
                    'time_type'  : 'leave'
                }))
                self.create_leaves_for_holidays(name, date_from_as_utc, date_to_as_utc, self.calendar_id.company_id)
            self.calendar_id.write({'global_leave_ids': global_leaves})

        return True

    def create_leaves_for_holidays(self, holiday_name, date_from, date_to, company):
        holiday_leaves = self.env['hr.leave'].search([('name', '=', holiday_name),('employee_company_id', '=', company.id)])
        if holiday_leaves:
            return True
        employee_list = self.env['hr.employee'].search([('company_id', '=', company.id), ('is_machine', '=', False)])
        time_difference = date_to - date_from
        days = math.ceil(time_difference.total_seconds() / (24 * 3600))
        for employee in employee_list:
            holiday_leave = self.env['hr.leave'].sudo().create({
                'name': holiday_name,
                'holiday_status_id': self.env.ref('canas.holiday_status_paid').id,
                'holiday_type': 'employee',
                'employee_id': employee.id,
                'request_date_from': date_from.strftime('%Y-%m-%d'),
                'request_date_to': date_to.strftime('%Y-%m-%d'),
                'date_to': date_to,
                'date_from': date_from,
                'number_of_days': days,
                'state': 'draft',

            })

        return True

