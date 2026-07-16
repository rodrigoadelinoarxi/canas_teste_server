from odoo import api, fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    reason = fields.Char(help="Reason for the status update", size=50, copy=False, readonly=True)


class AccountMoveReversal(models.TransientModel):
    _inherit = 'account.move.reversal'

    @api.model
    def _prepare_default_reversal(self, move):
        """
        Overrides to set reason instead of name when creating a refund
        """

        values = super(AccountMoveReversal, self)._prepare_default_reversal(move)
        values.update({
            'reason': self.reason
        })
        return values
