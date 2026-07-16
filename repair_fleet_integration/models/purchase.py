from odoo import fields, models


class PruchaseOrder(models.Model):
    _inherit = 'purchase.order'

    repair_id = fields.Many2one('repair.order', 'Repair')
    project_task_id = fields.Many2one('project.task', 'Work Number')
