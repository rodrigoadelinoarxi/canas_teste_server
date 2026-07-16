import logging
from datetime import datetime

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class RepairOrder(models.Model):
    _inherit = 'repair.order'

    @api.model
    def _default_stock_location(self):
        for location in self.env['stock.location'].search([]):
            if location.is_repairs_location:
                return location
        return False

    def _get_location_domain(self):
        locations = self.env['stock.location'].search([('is_repairs_location', '=', True)]).ids
        return [('id', 'in', locations)]

    location_id = fields.Many2one(
        'stock.location',
        'Location',
        default=_default_stock_location,
        index=True, readonly=True, required=True,
        help="This is the location where the product to repair is located.",
        states={'draft': [('readonly', False)], 'confirmed': [('readonly', True)]},
        domain=lambda self: self._get_location_domain()
    )

    fleet_vehicle = fields.Many2one('fleet.vehicle', string='Vehicle')
    product_id = fields.Many2one(
        'product.product',
        string='Product to Repair',
        readonly=True,
        required=False,
        states={'draft': [('readonly', False)]}
    )
    product_qty = fields.Float(
        'Product Quantity',
        default=1.0,
        digits='Product Unit of Measure',
        readonly=True,
        required=False,
        states={'draft': [('readonly', False)]}
    )
    product_uom = fields.Many2one(
        'uom.uom',
        'Product Unit of Measure',
        readonly=True,
        required=False,
        states={'draft': [('readonly', False)]}
    )
    purchase_order_ids = fields.One2many(
        'purchase.order',
        'repair_id',
        string="Purchase Orders",
        states={'done': [('readonly', True)]}
    )
    operation_type = fields.Many2one('stock.picking.type', compute='_compute_get_operation_type')
    total_purchases = fields.Integer(compute="_compute_total_purchases")

    @api.onchange('fleet_vehicle')
    def _on_change_vehicle(self):
        self.product_id = self.fleet_vehicle.product_id.product_variant_id

    @api.depends('location_id')
    def _compute_get_operation_type(self):
        warehouse = self.location_id.warehouse_id
        self.operation_type = self.env['stock.picking.type'].search(
            [('warehouse_id', '=', warehouse.id), ('code', 'like', 'incoming')], limit=1
        )

    def _compute_total_purchases(self):
        for record in self:
            record.total_purchases = record.env['purchase.order'].search_count([('repair_id', '=', record.id)])

    def action_repair_end(self):
        res = super(RepairOrder, self).action_repair_end()
        self.env['fleet.vehicle.log.services'].sudo().create({
            'amount': self.amount_total,
            'date': datetime.now(),
            'vehicle_id': self.fleet_vehicle.id,
            'service_type_id': self.env.ref('repair_fleet_integration.repair_service').id,
            'repair_id': self.id
        })
        return res

    def action_view_purchase(self):
        tree_id = self.env.ref('purchase.purchase_order_tree').id
        form_id = self.env.ref('purchase.purchase_order_form').id
        search_id = self.env.ref('purchase.view_purchase_order_filter').id
        return {
            'type': 'ir.actions.act_window',
            'name': _('List of Purchases For This Repair'),
            'view_mode': 'tree,form',
            'res_model': 'purchase.order',
            'domain': str([('repair_id', 'in', self.ids)]),
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'context': {
                'default_repair_id': self.id,
                'default_picking_type_id': self.operation_type.id,
                'default_origin': self.name},
            'search_view_id': search_id,
        }
