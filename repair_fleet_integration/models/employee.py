from odoo import fields, models, _
from odoo.exceptions import ValidationError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    is_machine = fields.Boolean('Is A Machine')
    employee_number = fields.Char('Employee Number')
    epi_picking_ids = fields.One2many('stock.picking', 'employee_id', "Employee EPIs")
    total_moves = fields.Integer(compute="_compute_total_moves")

    def action_view_epi_stock_move_lines(self):
        self.ensure_one()
        if not self.address_id:
            raise ValidationError(_('Please insert work address'))
        operation = self.env['stock.picking.type'].search([('is_delivery_epi_operation', '=', True)], limit=1)
        action = self.env["ir.actions.actions"]._for_xml_id("stock.stock_picking_action_picking_type")
        action['context'] = {
            'search_default_picking_type_id': operation.id,
            'default_partner_id': self.address_id.id,
            'default_employee_id': self.id
        }
        action['domain'] = [('id', 'in', self.epi_picking_ids.ids)]
        return action

    def _compute_total_moves(self):
        for record in self:
            record.total_moves = record.env['stock.move'].search_count([('create_uid', '=', record.user_id.id)])
