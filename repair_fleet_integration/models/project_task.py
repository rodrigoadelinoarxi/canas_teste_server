import logging

from odoo import api, fields, models, _, exceptions

_logger = logging.getLogger(__name__)


class Task(models.Model):
    _inherit = 'project.task'

    def _get_default_warehouse_domain(self):
        wh = self.env['stock.warehouse'].search([('code', '=', 'EST')], limit=1)
        domain = []
        if wh and wh.lot_stock_id:
            domain = [('id', 'in', wh.lot_stock_id.ids)]
        return domain

    location_id = fields.Many2one(
        'stock.location',
        domain=lambda self: self._get_default_warehouse_domain(),
        readonly=1
    )

    # --- vehicle timesheet ---
    vehicle_planned_hours = fields.Float(tracking=True)
    vehicle_progress = fields.Float(compute='_compute_vehicle_progress_hours', store=True)
    vehicle_effective_hours = fields.Float(
        'Effective hours',
        compute='_compute_vehicle_effective_hours',
        compute_sudo=True,
        store=True
    )
    vehicle_remaining_hours = fields.Float(
        compute='_compute_vehicle_remaining_hours',
        store=True,
        readonly=True,
        help='Total remaining time, can be re-estimated periodically by the assignee of the task.'
    )
    vehicle_timesheet_ids = fields.One2many(
        'account.analytic.line', 'task_id',
        'Vehicle Timesheets',
        domain=[('fleet_vehicle_id', '!=', False)]
    )
    timesheet_ids = fields.One2many(domain=[('fleet_vehicle_id', '=', False)])
    purchase_ids = fields.One2many('purchase.order', 'project_task_id', 'Purchase Orders')

    @api.depends('vehicle_effective_hours', 'vehicle_planned_hours')
    def _compute_vehicle_remaining_hours(self):
        for task in self:
            task.vehicle_remaining_hours = task.vehicle_planned_hours - task.vehicle_effective_hours

    @api.depends('vehicle_effective_hours', 'vehicle_planned_hours')
    def _compute_vehicle_progress_hours(self):
        for task in self:
            if task.vehicle_planned_hours > 0:
                if task.vehicle_effective_hours > task.vehicle_planned_hours:
                    task.vehicle_progress = 100
                else:
                    task.vehicle_progress = round(100.0 * task.vehicle_effective_hours / task.vehicle_planned_hours, 2)
            else:
                task.vehicle_progress = 0.0

    @api.depends('vehicle_timesheet_ids.unit_amount')
    def _compute_vehicle_effective_hours(self):
        for task in self:
            task.vehicle_effective_hours = round(sum(task.vehicle_timesheet_ids.mapped('unit_amount')), 2)

    # --- end vehicle timesheet ---

    def action_create_shipyard(self):
        if not self.env['stock.warehouse'].search([('code', '=', 'EST')]):
            raise exceptions.UserError(_('The reference warehouse for the shipyards was not found'))
        location = self.env['stock.location'].search([('name', '=', self.name), ('location_id', '=', 'EST')]).id
        if not location:
            self.location_id = self.env['stock.location'].create({
                'name': self.name,
                'location_id': self.env['stock.location'].search([('name', '=', 'EST')], limit=1).id,
                'usage': 'internal',
                'task_id': self.id
            }).id
        else:
            self.location_id = location

    def action_delete_shipyard(self):
        try:
            self.location_id.unlink()
        except Exception as error:
            _logger.error(error)
            self.write({'active': False})

    def action_get_stock(self):
        """
        Returns an action with stock of this task
        """
        action = self.env.ref('stock.location_open_quants').read()[0]
        action['domain'] = [('location_id', '=', self.location_id.id), ('quantity', '>', 0)]
        action['context'] = ''
        return action
