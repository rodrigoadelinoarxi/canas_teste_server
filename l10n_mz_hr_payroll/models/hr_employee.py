from odoo import models, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    subject_to_social_security = fields.Boolean("Subject to Social Security?", default=True)
