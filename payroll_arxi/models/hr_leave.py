from odoo import models, fields
from datetime import datetime, timedelta, time
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY


class HrLeave(models.Model):
    _inherit = 'hr.leave'

    def _get_number_of_days(self, date_from, date_to, employee_id):
        time_between = date_from - date_to
        d = time_between.days
        h = time_between.seconds / 3600

        return {'days': abs(d), 'hours': h}


