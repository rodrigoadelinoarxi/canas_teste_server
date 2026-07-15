import logging

from odoo import models

_logger = logging.getLogger(__name__)


class HolidayWizard(models.TransientModel):
    _inherit = 'holiday.wizard'
    _description = 'Wizard to get national holidays'

    def action_get_holidays(self):
        super(HolidayWizard, self).action_get_holidays()
        for rec in self:
            rec.calendar_id.global_leave_ids.write({
                'work_entry_type_id': self.env.ref('canas.holiday_entry_type', raise_if_not_found=False)
            })
