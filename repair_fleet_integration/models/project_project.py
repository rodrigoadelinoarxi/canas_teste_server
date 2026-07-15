from odoo import models, fields, api


class Project(models.Model):
    _inherit = 'project.project'

    location = fields.Char()

    @api.model
    def create(self, vals):
        project = super(Project, self).create(vals)
        self.env['project.task'].create({
            'project_id': project.id,
            'name': 'Obra nº: %s - %s' % (project.name, project.location)
        })
        return project
