from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.osv import expression


class FleetVehicle(models.Model):
    _inherit = 'fleet.vehicle'

    total_repairs = fields.Integer(compute="_compute_total_repairs")
    product_id = fields.Many2one('product.template', 'Associate Product', readonly=1)
    equipment_code = fields.Many2one('equipment.code', required=True)
    location_id = fields.Many2one('stock.warehouse', 'Stock Location')
    computed_location_id = fields.Many2one('stock.location', 'Current Location', compute="_compute_current_location")
    cost_price = fields.Float('Cost Price/Hour')
    state_tag = fields.Selection(
        [('repairs', 'REPAIR'), ('not_in_use', 'STOPPED'), ('in_use', 'IN USE')], compute="_compute_get_state"
    )

    def _compute_current_location(self):
        for rec in self:
            rec.computed_location_id = self.env['stock.quant'].search(
                [('product_id', '=', rec.product_id.product_variant_id.id),
                 ('quantity', '=', 1.0)], limit=1).location_id.id

    @api.depends('computed_location_id')
    def _compute_get_state(self):
        for rec in self:
            if rec.computed_location_id.is_repairs_location:
                rec.state_tag = 'repairs'
            elif rec.computed_location_id.task_id:
                rec.state_tag = 'in_use'
            else:
                rec.state_tag = 'not_in_use'

    def unlink(self):
        for rec in self:
            self.env['stock.change.product.qty'].create({
                'product_id': rec.product_id.product_variant_id.id,
                'product_tmpl_id': rec.product_id.id,
                'new_quantity': 0,
            }).change_product_qty()
            rec.product_id.write({'active': False})
            return super(FleetVehicle, self).unlink()

    @api.model_create_multi
    def create(self, vals_list):
        equipment_code = False
        for vals in vals_list:
            if vals.get('equipment_code'):
                equipment_code = self.env['equipment.code'].browse(vals.get('equipment_code'))
                if equipment_code.equipment_id:
                    raise ValidationError(
                        _("The selected equipment code is already associated to the vehicle/equipment {}").format(
                            equipment_code.equipment_id.name))
            name = self.env['fleet.vehicle.model'].browse(vals.get('model_id'))
            vals['name'] = name.brand_id.name + '/' + name.name + '/' + (
                    vals.get('license_plate') or _('No Plate')) + '/' + (equipment_code.name or _('No equipment Code'))
            vals['product_id'] = self.env['product.template'].sudo().create({
                'name': vals.get('name'),
                'default_code': equipment_code.name,
                'sale_ok': False,
                'purchase_ok': False,
                'type': 'product',
                'categ_id': self.env['product.category'].search([('is_vehicle_categ', '=', True)], limit=1).id,
                'list_price': 0.00,
                'standard_price': vals.get('cost_price'),
                'taxes_id': None,
            }).id
            self.env['hr.employee'].sudo().create({
                'name': vals.get('name'),
                'is_machine': True,
                'employee_number': equipment_code.name
            })
        res = super(FleetVehicle, self).create(vals_list)
        if equipment_code:
            equipment_code.equipment_id = res.id

        for vehicle_id in res:
            vehicle_id.product_id.write({'vehicle_id': vehicle_id.id})
            self.env['stock.change.product.qty'].create({
                'product_id': vehicle_id.product_id.product_variant_id.id,
                'product_tmpl_id': vehicle_id.product_id.id,
                'new_quantity': 1,
            }).change_product_qty()
            vehicle_id.computed_location_id = vehicle_id.location_id.lot_stock_id.id
        return res

    def write(self, vals):
        for vehicle in self:
            if vehicle.product_id and vals.get('cost_price'):
                vehicle.product_id.write({'standard_price': vals['cost_price']})
            if vals.get('equipment_code'):
                equipment_code = self.env['equipment.code'].browse(vals.get('equipment_code'))
                if equipment_code.equipment_id:
                    raise ValidationError(
                        _("The selected equipment code is already associated to the vehicle/equipment {}").format(
                            equipment_code.equipment_id.name))
                if vehicle.equipment_code:
                    vehicle.equipment_code.equipment_id = False
                equipment_code.equipment_id = vehicle.id
        return super(FleetVehicle, self).write(vals)

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        domain = args or []
        if not domain:
            domain = expression.AND([domain, ['|', ('name', operator, name), ('equipment_code', operator, name)]])
        return self._search(domain, limit=limit, access_rights_uid=name_get_uid)

    def _compute_total_repairs(self):
        for record in self:
            record.total_repairs = record.env['repair.order'].search_count([('fleet_vehicle', '=', record.id)])

    def action_view_repair(self):
        tree_id = self.env.ref('repair.view_repair_order_tree').id
        form_id = self.env.ref('repair.view_repair_order_form').id
        search_id = self.env.ref('repair.view_repair_order_form_filter').id
        return {
            'type': 'ir.actions.act_window',
            'name': _('List of Repairs'),
            'view_mode': 'tree,form',
            'res_model': 'repair.order',
            'domain': [('fleet_vehicle', 'in', self.ids)],
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'search_view_id': search_id,
        }

    def action_view_fleet_stock_move_lines(self):
        self.ensure_one()
        action = self.env.ref('stock.stock_move_line_action').read()[0]
        action['domain'] = [('product_id', '=', self.product_id.id)]
        return action

    def action_view_timesheet_reports(self):
        tree_id = self.env.ref('repair_fleet_integration.timesheet_view_tree_fleet_vehicle').id
        form_id = self.env.ref('analytic.view_account_analytic_line_form').id
        search_id = self.env.ref('repair_fleet_integration.fleet_vehicle_timesheet_view_search').id
        return {
            'type': 'ir.actions.act_window',
            'name': _('Vehicle Timesheets'),
            'view_mode': 'tree,form',
            'res_model': 'account.analytic.line',
            'domain': str([('project_id', '!=', False), ('fleet_vehicle_id', 'in', self.ids)]),
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'search_view_id': search_id,
        }


class FleetVehicleLogServices(models.Model):
    _inherit = 'fleet.vehicle.log.services'

    repair_id = fields.Many2one('repair.order')
    liter = fields.Float()
    price_per_liter = fields.Float()


class EquipmentCode(models.Model):
    _name = 'equipment.code'
    _description = 'Equipment Code'

    name = fields.Char('Equipment Code', required=True)
    equipment_id = fields.Many2one('fleet.vehicle', 'Equipment/Vehicle', readonly=True)

    _sql_constraints = [
        ('equipment_code_unique', 'unique(name)', _('Equipment code already exists'))
    ]
