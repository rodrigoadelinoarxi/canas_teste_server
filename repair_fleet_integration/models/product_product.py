from odoo import models, fields, api, _


class ProductProduct(models.Model):
    _inherit = 'product.product'

    equipment_code_required = fields.Boolean(related='product_tmpl_id.equipment_code_required', readonly=False)
    default_code = fields.Char(
        required=True,
        tracking=True,
        default='/',
        help="Set to '/' and save if you want a new internal reference to be proposed."
    )

    @api.model
    def create(self, vals):
        if 'default_code' not in vals or vals['default_code'] == '/':
            categ_id = vals.get('categ_id')
            template_id = vals.get('product_tmpl_id')
            categ = sequence = False
            if categ_id:
                # Created as a product.product
                categ = self.env['product.category'].browse(categ_id)
            elif template_id:
                # Created from a product.template
                template = self.env['product.template'].browse(template_id)
                categ = template.categ_id
            if categ:
                sequence = categ.sequence_id
            if not sequence:
                sequence = self.env.ref('repair_fleet_integration.seq_product_auto')
            vals['default_code'] = sequence.next_by_id()
        return super(ProductProduct, self).create(vals)

    def write(self, vals):
        """To assign a new internal reference, just write '/' on the field.
        Note this is up to the user, if the product category is changed,
        she/he will need to write '/' on the internal reference to force the
        re-assignment."""
        for product in self:
            if vals.get('default_code', '') == '/':
                category_id = vals.get('categ_id', product.categ_id.id)
                category = self.env['product.category'].browse(category_id)
                sequence = category.sequence_id
                if not sequence:
                    sequence = self.env.ref('repair_fleet_integration.seq_product_auto')
                ref = sequence.next_by_id()
                vals['default_code'] = ref
                if len(product.product_tmpl_id.product_variant_ids) == 1:
                    product.product_tmpl_id.write({'default_code': ref})
        return super(ProductProduct, self).write(vals)

    def copy(self, default=None):
        if default is None:
            default = {}
        if self.default_code:
            default.update({
                'default_code': self.default_code + _('-copy'),
            })
        return super(ProductProduct, self).copy(default)
