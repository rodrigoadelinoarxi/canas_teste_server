from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    vat = fields.Char("VAT")
    niss = fields.Char("NISS")
    establishment_id = fields.Many2one('res.branch', "Branch")
    establishment_ssc = fields.Char(related='establishment_id.ssc')
    insurance = fields.Char()
    policy_number = fields.Char()
    is_unionized = fields.Boolean("Unionized")
    is_occasional = fields.Boolean("Occasional")

    @api.model
    def create(self, vals):
        res = super(HrEmployee, self).create(vals)
        res.insurance = self.env['res.company'].browse(res.company_id.id).insurance_company
        res.policy_number = self.env['res.company'].browse(res.company_id.id).insurance_policy
        return res
