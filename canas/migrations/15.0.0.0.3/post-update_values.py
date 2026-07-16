from odoo import api, SUPERUSER_ID


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    for project in env['project.project'].search([]):
        project.description = project.project_description
        project.date_start = project.date_from
        project.date = project.date_to

    for partner_id in env['res.partner'].search([]):
        if partner_id.supplier_code:
            partner_id.ref = partner_id.supplier_code

    for purchase_id in env['purchase.order'].search([]):
        purchase_id.work_project_id = purchase_id.x_studio_field_F3KGu.id
        purchase_id.pre_payment = purchase_id.x_studio_pr_pagamento
        purchase_id.is_import = purchase_id.x_studio_e_importacao
        for line_id in purchase_id.order_line:
            line_id.is_request = line_id.x_studio_pedido

    for repair_id in env['repair.order'].search([]):
        repair_id.invoice_method = 'none'
