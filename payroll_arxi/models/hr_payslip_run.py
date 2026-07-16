from odoo import models, fields, api, _
from odoo import Command
import logging

from odoo.fields import Date
from odoo.tools import html2plaintext, date_utils
from datetime import date, datetime
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class Payslip(models.Model):
    _inherit = 'hr.payslip.run'

    warning_message = fields.Char(readonly=True, default=False)

    date_start = fields.Date(string='Date From', required=True, readonly=True,
                             states={'draft': [('readonly', False)]},
                             default=lambda self: fields.Date.to_string(
                                 (datetime.now() + relativedelta(months=-1, day=21)).date()),
                             )
    date_end = fields.Date(string='Date To', required=True, readonly=True,
                           states={'draft': [('readonly', False)]},
                           default=lambda self: fields.Date.to_string(date.today().replace(day=20)),
                           )

    def _compute_warning_message(self):
        print("compute")
        for slip in self:
            if any(entry.state == 'draft' for entry in self.env['hr.work.entry'].search([])):
                slip.warning_message = _(
                    "There are non validated work entries! "
                )
            else:
                slip.warning_message = False