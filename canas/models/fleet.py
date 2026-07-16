from odoo import fields, models


class FleetVehicleLogServices(models.Model):
    _inherit = 'fleet.vehicle.log.services'

    project_id = fields.Many2one('project.project')
