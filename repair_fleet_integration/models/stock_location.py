from odoo import models, fields, api


class StockLocation(models.Model):
    _inherit = 'stock.location'

    task_id = fields.Many2one('project.task')
    is_repairs_location = fields.Boolean()
    is_employee_stock_location = fields.Boolean()
    allowed_user_ids = fields.Many2many('res.users', 'location_security_stock_location_users', 'location_id', 'user_id')

    def write(self, vals):
        if vals.get('allowed_user_ids'):
            old = self.allowed_user_ids.ids
            new = vals.get('allowed_user_ids')[0][2]
            if self.location_id.usage == 'view' or self.location_id.usage == 'transit':
                diference_add = list(set(new) - set(old))
                for u in diference_add:
                    user = self.env['res.users'].browse(u)
                    user.sudo().write({'stock_location_ids': [(4, self.location_id.id)]})
                diference_remove = list(set(old) - set(new))
                for u in diference_remove:
                    user = self.env['res.users'].browse(u)
                    if not any(location_id in user.stock_location_ids.ids for location_id in
                               self.location_id.child_ids.ids):
                        user.sudo().write({'stock_location_ids': [(3, self.location_id.id)]})
        return super(StockLocation, self).write(vals)

    @api.model
    def create(self, vals):
        res = super(StockLocation, self).create(vals)
        if vals.get('allowed_user_ids'):
            if res.location_id.usage == 'view' or res.location_id.usage == 'transit':
                for u in vals.get('allowed_user_ids')[0][2]:
                    user = self.env['res.users'].browse(u)
                    user.sudo().write({'stock_location_ids': [(4, res.location_id.id)]})
        return res
