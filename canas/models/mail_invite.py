from odoo import models, fields


class MailInvite(models.TransientModel):
    _inherit = 'mail.wizard.invite'

    def _compute_partner_domain(self):
        if self._context and self._context['default_res_model'] and self._context['default_res_model'] == 'project.project':
            employee_categ_id = self.env.ref('canas.res_partner_employee_category').id
            employee_ids = self.env['res.partner'].search([('category_id', '=', employee_categ_id)]).ids
            return [('id', 'in', employee_ids)]
        return []

    partner_ids = fields.Many2many(
        'res.partner',
        string='Recipients',
        help="List of partners that will be added as follower of the current document.",
        domain=_compute_partner_domain
    )
