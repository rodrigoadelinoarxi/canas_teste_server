from odoo import models, api, fields


class AccountCancelWizard(models.TransientModel):
    _name = 'account.cancel.wizard'
    _description = 'Wizard to cancel a document'

    reason = fields.Char(required=True, size=50)

    def cancel_move(self):
        context = dict(self._context or {})
        move = self.env['account.move'].browse(context.get('active_id'))

        if move.state not in ('draft', 'cancel'):
            # Cancels the invoice and set the reason why the invoice was canceled
            move.write({
                'reason': self.reason,
            })
            move.button_cancel()

    def cancel_payment(self):
        context = dict(self._context or {})
        payment = self.env['account.payment'].browse(context.get('active_id'))

        if payment.state not in ('draft', 'cancel'):
            # Cancels the invoice and set the reason why the invoice was canceled
            payment.write({
                'reason': self.reason,
            })

        # We need to perform more actions that are described in `action_invoice_cancel` method
            payment.action_cancel()
