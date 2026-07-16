import logging

from odoo import models
from odoo.exceptions import AccessError

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _update_supplier_in_product(self):
        """
        Updates last created supplier info with discount values
        """
        for line in self.order_line.filtered('product_id'):
            partner = self.partner_id.commercial_partner_id
            currency = self.currency_id or self.env.company.currency_id

            # Do not add a contact as a supplier
            supplierinfos = line.product_id.seller_ids.filtered(lambda i: i.name == partner)

            if partner not in line.product_id.seller_ids.mapped('name') and len(line.product_id.seller_ids) <= 10:
                supplierinfo = line._prepare_values_for_supplierinfo_create(currency, partner)
                # In case the order partner is a contact address, a new supplierinfo is created on
                # the parent company. In this case, we keep the product name and code.
                seller = line.product_id._select_seller(
                    partner_id=line.partner_id,
                    quantity=line.product_qty,
                    date=line.order_id.date_order and line.order_id.date_order.date(),
                    uom_id=line.product_uom)
                if seller:
                    supplierinfo['product_name'] = seller.product_name
                    supplierinfo['product_code'] = seller.product_code
                vals = {
                    'seller_ids': [(0, 0, supplierinfo)],
                }
                try:
                    line.product_id.write(vals)
                except AccessError:  # no write access rights -> just ignore
                    break
            for supplier in supplierinfos:
                supplier.write(line._prepare_vals_for_supplierinfo_update(currency))

    def button_confirm(self):
        res = super(PurchaseOrder, self).button_confirm()
        for order in self.filtered(lambda o: o.state in ('to approve', 'purchase')):
            order._update_supplier_in_product()
        return res


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    def _prepare_values_for_supplierinfo_create(self, currency, partner):
        values = {
            'name'       : partner.id,
            'currency_id': currency.id,
            'delay'      : 0,
            'sequence'   : max(
                self.product_id.seller_ids.mapped('sequence')) + 1 if self.product_id.seller_ids else 1,
            'product_uom': self.product_uom.id,
            'min_qty'    : 0.0,
            'price'      : self.product_qty and (self.price_subtotal / self.product_qty) or 0.0
        }
        if hasattr(self.env['product.supplierinfo'], 'price_without_discount'):
            values.update({
                'price_without_discount': self.price_unit
            })
            if hasattr(self, 'first_discount'):
                values.update({
                    'first_discount': self.first_discount or 0.0
                })
            if hasattr(self, 'second_discount'):
                values.update({
                    'second_discount': self.second_discount or 0.0
                })
        return values

    def _prepare_vals_for_supplierinfo_update(self, currency):
        values = {
            'currency_id': currency.id,
            'price'      : self.product_qty and (self.price_subtotal / self.product_qty) or 0.0
        }
        if hasattr(self.env['product.supplierinfo'], 'price_without_discount'):
            values.update({
                'price_without_discount': self.price_unit
            })
            if hasattr(self, 'first_discount'):
                values.update({
                    'first_discount': self.first_discount or 0.0
                })
            if hasattr(self, 'second_discount'):
                values.update({
                    'second_discount': self.second_discount or 0.0
                })
        return values
