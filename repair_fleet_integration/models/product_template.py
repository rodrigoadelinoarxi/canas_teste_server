from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    equipment_code_required = fields.Boolean('Require Equipment Code')
    vehicle_id = fields.Many2one('fleet.vehicle', readonly=1, ondelete='cascade')

    @api.model
    def create(self, vals):
        if self.vehicle_id:
            vals.vehicle_id = self.vehicle_id
        res = super(ProductTemplate, self).create(vals)
        if 'categ_id' in vals.keys():
            category = self.env['product.category'].browse(vals.get('categ_id'))
            if res.product_variant_id:
                res.product_variant_id.equipment_code_required = category.is_mechanic_categ
            else:
                res.equipment_code_required = category.is_mechanic_categ
        return res

    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        if 'categ_id' in vals.keys():
            category = self.env['product.category'].browse(vals.get('categ_id'))
            self.product_variant_id.equipment_code_required = category.is_mechanic_categ
        return res

    @api.onchange('vehicle_id')
    def _on_change_vehicle_id(self):
        if self.vehicle_id:
            self.update({
                'name': self.vehicle_id.name,
                'sale_ok': False,
                'purchase_ok': False,
                'type': 'product',
                'categ_id': self.env['product.category'].search([('is_vehicle_categ', '=', True)], limit=1),
                'list_price': 0.00,
                'taxes_id': None,
                'route_ids': None
            })
