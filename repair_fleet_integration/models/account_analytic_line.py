from odoo import api, fields, models


class AccountAnalyticLine(models.Model):
    _inherit = 'account.analytic.line'
    _order = "create_date"

    fleet_vehicle_id = fields.Many2one('fleet.vehicle')

    @api.model
    def create(self, vals):
        if vals.get('fleet_vehicle_id'):
            vals['product_id'] = self.env['fleet.vehicle'].browse(vals.get('fleet_vehicle_id')).product_id.product_variant_id.id
        return super(AccountAnalyticLine, self).create(vals)

    def write(self, vals):
        if vals.get('fleet_vehicle_id'):
            vals['product_id'] = self.env['fleet.vehicle'].browse(vals.get('fleet_vehicle_id')).product_id.product_variant_id.id
        return super(AccountAnalyticLine, self).write(vals)

    def _timesheet_postprocess_values(self, values):
        result = {id_: {} for id_ in self.ids}
        sudo_self = self.sudo()
        if any([field_name in values for field_name in ['unit_amount', 'employee_id', 'account_id']]):
            for timesheet in sudo_self:
                if self.fleet_vehicle_id:
                    cost = self.fleet_vehicle_id.cost_price or 0.0
                else:
                    cost = timesheet.employee_id.timesheet_cost or 0.0
                amount = -timesheet.unit_amount * cost
                amount_converted = timesheet.employee_id.currency_id._convert(
                    amount, timesheet.account_id.currency_id, self.env.user.company_id, timesheet.date)
                result[timesheet.id].update({
                    'amount': amount_converted,
                })
        return result
