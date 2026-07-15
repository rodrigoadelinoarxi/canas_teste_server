from odoo import models
try:
    import holidays
except ImportError:
    raise ImportError('This module needs holidays installed on your system. (pip3 install holidays)')


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    def action_get_national_holidays(self):
        self.ensure_one()
        return self.env['ir.actions.act_window']._for_xml_id('hr_national_holidays.holiday_wizard_action')
