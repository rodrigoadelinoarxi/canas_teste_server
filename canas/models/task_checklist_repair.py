from odoo import fields, models, api


class TaskChecklistRepair(models.Model):
    _name = 'task.checklist.repair'
    _description = 'Task Checklist'
    _order = 'repair_id, sequence, id'

    def _get_defualt_user(self):
        return self.repair_id.responsible_id if self.repair_id and self.repair_id.responsible_id else False

    sequence = fields.Integer(
        help='Gives the sequence order when displaying a list',
        default=10
    )
    name = fields.Char(required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Completed'),
        ('cancel', 'Cancelled'),
    ], default='draft', copy=False)
    user_id = fields.Many2one('hr.employee', string='Assigned to', default=_get_defualt_user)
    repair_id = fields.Many2one('repair.order', 'Repair', required=True, ondelete='cascade')

    def action_done(self):
        self.state = 'done'

    def action_cancel(self):
        self.state = 'cancel'

    def action_draft(self):
        self.state = 'draft'
