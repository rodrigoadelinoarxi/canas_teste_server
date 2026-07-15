from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    branch_ids = fields.One2many('res.branch', 'company_id', "Branches")
    insurance_company = fields.Char(str="Insurance Company")
    insurance_policy = fields.Char(str="Insurance Policy")

    def write(self,vals):
        res = super(ResCompany,self).write(vals)
        for company in self:
            employees = self.env['hr.employee'].search([('company_id','=',company.id)])
            for rec in employees:
                rec.insurance = company.insurance_company
                rec.policy_number = company.insurance_policy
        return res


class ResBranch(models.Model):
    _name = 'res.branch'

    company_id = fields.Many2one('res.company')
    name = fields.Char()
    ssc = fields.Char("Social Security Code")
