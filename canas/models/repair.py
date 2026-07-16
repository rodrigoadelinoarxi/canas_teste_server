from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, fields, Command, models, _
from odoo.exceptions import ValidationError


class Repair(models.Model):
    _inherit = 'repair.order'

    @api.depends('task_checklist_ids', 'task_checklist_ids.state')
    def _compute_checklist_done(self):
        for rec in self:
            if rec.task_checklist_ids:
                done_checklist = 0
                for checklist in rec.task_checklist_ids:
                    if checklist.state in ['done', 'cancel']:
                        done_checklist += 1
                rec.checklist_done = (done_checklist * 100) / len(rec.task_checklist_ids)

    original_location = fields.Many2one('stock.location', 'Original Location')
    code_equipment_related = fields.Char('Equipment Code', related='fleet_vehicle.equipment_code.name')
    responsible_id = fields.Many2one('hr.employee')
    checklist_done = fields.Float(compute='_compute_checklist_done', store=True)
    task_checklist_ids = fields.One2many('task.checklist.repair', 'repair_id', 'Repair')

    # timesheet info
    task_id = fields.Many2one('project.task')
    project_id = fields.Many2one('project.project', related='task_id.project_id')
    analytic_account_active = fields.Boolean(related='project_id.analytic_account_id.active')
    allow_timesheets = fields.Boolean(related='task_id.project_id.allow_timesheets')
    planned_hours = fields.Float(related='task_id.planned_hours')
    subtask_planned_hours = fields.Float(related='task_id.subtask_planned_hours')
    subtask_effective_hours = fields.Float(related='task_id.subtask_effective_hours')
    subtask_count = fields.Integer(related='task_id.subtask_count')

    total_hours_spent = fields.Float(related='task_id.total_hours_spent')
    remainqing_hours = fields.Float(related='task_id.remaining_hours')
    effective_hours = fields.Float(related='task_id.effective_hours')
    progress = fields.Float(related='task_id.progress')
    timesheet_ids = fields.One2many('account.analytic.line', 'repair_id', 'Timesheets')

    @api.model_create_multi
    def create(self, vals_list):
        res = super(Repair, self).create(vals_list)
        for rec in res:
            rec.task_id = self.env['project.task'].sudo().create({
                'name': rec.name,
                'project_id': self.env.ref('canas.repair_project').id
            })
        return res

    @api.onchange('fleet_vehicle')
    def set_original_location(self):
        for rec in self:
            product_id = rec.fleet_vehicle.product_id.id
            if product_id:
                last_stock_move = self.env['stock.move.line'].search(
                    [('product_id', '=', product_id)], order='date desc', limit=1).filtered(
                    lambda line: not line.location_dest_id.is_repairs_location)
                if last_stock_move:
                    location = last_stock_move.location_dest_id
                else:
                    location = rec.fleet_vehicle.computed_location_id
                rec.original_location = location

    def generate_purchase_order(self):
        purchase_id = self.env['purchase.order'].create({
            'partner_id': self.env.user.partner_id.id,
            'repair_id': self.id,
            'order_line': [Command.create({
                'product_id': line.product_id.id,
                'name': line.product_id.name,
                'date_planned': datetime.now() + relativedelta(days=+30),
                'product_qty': line.product_uom_qty,
                'product_uom': line.product_id.uom_id.id,
                'price_unit': line.price_unit,
                'taxes_id': [Command.set(line.product_id.supplier_taxes_id.ids)]
            }) for line in self.fees_lines]
        })

        purchase_id.write({
            'order_line': [
                Command.link(self.env['purchase.order.line'].create({
                    'product_id': line.product_id.id,
                    'name': line.product_id.name,
                    'date_planned': datetime.now() + relativedelta(days=+30),
                    'product_qty': line.product_uom_qty if line.product_available_qty <= 0 else line.product_uom_qty - line.product_available_qty,
                    'product_uom': line.product_id.uom_id.id,
                    'price_unit': line.price_unit,
                    'taxes_id': [Command.set(line.product_id.supplier_taxes_id.ids)],
                    'order_id': purchase_id.id,
                }).id) for line in self.operations.filtered(lambda c: c.product_uom_qty > c.product_available_qty)
            ],
        })

        if not purchase_id.order_line:
            raise ValidationError(_("Please fill lines in the repair!"))
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Order',
            'view_mode': 'form',
            'view_id': self.env.ref('canas.purchase_order_form_view_override', False).id,
            'res_model': 'purchase.order',
            'res_id': purchase_id.id,
            'target': 'new'
        }


class RepairLine(models.Model):
    _inherit = 'repair.line'

    product_available_qty = fields.Float(
        'Available Product Quantity',
        digits='Product Unit of Measure',
        related='product_id.qty_available'
    )
