from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HrContract(models.Model):
    _inherit = 'hr.contract'

    food_allowance = fields.Monetary()
    transport_allowance = fields.Monetary()

    employee_vat = fields.Char(related='employee_id.vat')
    employee_niss = fields.Char(related='employee_id.niss')
    establishment_ssc = fields.Char(related='employee_id.establishment_id.ssc')
    employee_insurance = fields.Char(related='employee_id.insurance')
    employee_policy_number = fields.Char(related='employee_id.policy_number')

    employee_establishment = fields.Many2one('res.branch', related='employee_id.establishment_id')
    transfer_ids = fields.One2many('hr.contract.transfer', inverse_name='contract_id')

    employee_children = fields.Integer(related='employee_id.children')

    employee_is_unionized = fields.Boolean(related='employee_id.is_unionized')
    employee_is_occasional = fields.Boolean(related='employee_id.is_occasional')

    assiduity_bonus = fields.Float()
    productivity_bonus = fields.Float()
    maintenance_bonus = fields.Float()

    contract_history_count = fields.Integer(compute="_compute_contract_count")

    def _compute_contract_count(self):
        for rec in self:
            contract = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)])
            if contract:
                rec.contract_history_count = len(contract)
            else:
                rec.contract_history_count = 0

    def write(self, vals):
        res = super(HrContract, self).write(vals)
        for rec in self:
            if len(rec.transfer_ids) > 0:
                if no_date_transf := rec.transfer_ids.filtered(lambda transf: not transf.transfer_end_date):
                    # TODO Case client want to insert multiple lines with automatic end data comment this condition
                    if len(rec.transfer_ids) > 2 and len(no_date_transf) > 2:
                        raise ValidationError(
                            _("Can't be more than one construction transferation open at the same time. \n"
                              "Correct construction transferation dates"))
                    elif self.new_transfer_validation():
                        raise ValidationError(
                            _("Construction transfer date can't be before or at the same date as the construction transfer end or start date before."))
                    else:
                        for transf_id in no_date_transf:

                            list_transfs = self.get_transfer_index_list(rec)
                            if not list_transfs.index(transf_id.id) + 1 > len(rec.transfer_ids) - 1:
                                if start_date_rec := rec.transfer_ids[list_transfs.index(transf_id.id) + 1]:
                                    transf_id.transfer_end_date = start_date_rec.transfer_start_date - timedelta(days=1)
        return res

    # Return list of index of the rec transfer_ids from the record pass
    def get_transfer_index_list(self, rec):
        list_transfs = []
        for record in rec.transfer_ids:
            list_transfs += [record.id]

        return list_transfs

    # Validate new transfer start date it's greater than the last close transfer
    def new_transfer_validation(self):
        new_transfer_valid = False
        for rec in self:
            if no_date_transfers := rec.transfer_ids.filtered(lambda transf: not transf.transfer_end_date):
                if not (len(no_date_transfers) == 1 and len(rec.transfer_ids) == 1):
                    list_transfers = self.get_transfer_index_list(rec)
                    for no_date_transfer in no_date_transfers:
                        if last_transfer_end_date := rec.transfer_ids[
                            list_transfers.index(no_date_transfer.id) - 1].transfer_end_date:
                            new_transfer_valid = no_date_transfer.transfer_start_date <= last_transfer_end_date
                        else:
                            new_transfer_valid = no_date_transfer.transfer_start_date <= rec.transfer_ids[
                                list_transfers.index(no_date_transfer.id) - 1].transfer_start_date
        return new_transfer_valid

    def action_open_contracts(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("hr_contract.action_hr_contract")
        action.update({'domain': [('employee_id', '=', self.employee_id.id)]})
        return action


class HrContractConstructionTransfer(models.Model):
    _name = 'hr.contract.transfer'

    is_deslocated = fields.Boolean()

    transfer_start_date = fields.Date(string='Transfer Construction Date', required=True)
    transfer_end_date = fields.Date(string='Transfer Construction End Date')

    contract_id = fields.Many2one('hr.contract', string='Contract', required=True, readonly=True)
    construction_id = fields.Many2one('project.project', string='Construction', required=True)
    analytic_account_id = fields.Many2one(related='construction_id.analytic_account_id', string='Analytic Account')
