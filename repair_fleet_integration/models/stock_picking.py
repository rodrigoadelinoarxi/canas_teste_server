from odoo import models, fields, api


class StockPikingType(models.Model):
    _inherit = 'stock.picking.type'

    is_delivery_epi_operation = fields.Boolean("It's a EPI's delivery operation")


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    employee_id = fields.Many2one('hr.employee', 'Employee')
    is_epi_delivery_operation = fields.Boolean(related='picking_type_id.is_delivery_epi_operation')
    is_employee_stock_location = fields.Boolean(related='location_dest_id.is_employee_stock_location')
    location_id = fields.Many2one('stock.location', domain="[('allowed_user_ids', 'in', uid)]")
    location_dest_id = fields.Many2one('stock.location', domain="[('allowed_user_ids', 'in', uid)]")

    def _action_done(self):
        for line in self.move_line_ids_without_package:
            if line.product_id.product_tmpl_id.vehicle_id:
                line.product_id.product_tmpl_id.vehicle_id.location_id = self.location_dest_id.warehouse_id
        return super(StockPicking, self)._action_done()

    @api.model
    def create(self, vals):
        res = super(StockPicking, self).create(vals)
        if res.is_epi_delivery_operation and res.is_employee_stock_location and res.employee_id:
            res.employee_id.epi_picking_ids |= res
        return res
