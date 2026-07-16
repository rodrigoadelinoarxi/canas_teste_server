import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class Project(models.Model):
    _inherit = 'project.project'

    # TO REMOVE AFTER MIGRATION
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    project_description = fields.Char('Project Description')
    # TO REMOVE AFTER MIGRATION

    is_repairs_project = fields.Boolean(string='Repair Project')
    proposal_nr = fields.Char('Proposal Nr.')
    contract_nr = fields.Char('Contract Nr.')
    company_currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)
    contract_value = fields.Monetary('Contract Value', currency_field='company_currency_id')
    construction_director = fields.Many2one('res.users', string='Construction Director')


class ProjectTask(models.Model):
    _inherit = 'project.task'

    original_location = fields.Many2one('stock.location', 'Original Location')
    repair_order = fields.Many2one('repair.order', 'Repair Order')
