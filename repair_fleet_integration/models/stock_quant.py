from odoo import models, api, _
from odoo.exceptions import UserError


class StockQuant(models.Model):
    _inherit = "stock.quant"

    @api.constrains('product_id', 'quantity')
    def check_negative_qty(self):
        for quant in self:
            if quant.quantity < 0 and quant.product_id.type == 'product' and quant.location_id.usage in ['internal', 'transit'] and self.location_id.company_id.no_negative_stock:
                msg_add = ''
                if quant.lot_id:
                    msg_add = _("lot '%s'") % quant.lot_id.name_get()[0][1]
                raise UserError(
                    _("It's not allowed negative stock on product: '%s''%s'. Make an inventory adjustment.") % (
                        self.product_id.name, msg_add))
