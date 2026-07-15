import logging

from odoo import models, fields

_logger = logging.getLogger(__name__)


class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _update_purchase_order_line(self, product_id, product_qty, product_uom, company_id, values, line):
        res = super(StockRule, self)._update_purchase_order_line(product_id, product_qty, product_uom, company_id, values, line)
        partner = values['supplier'].name
        procurement_uom_po_qty = product_uom._compute_quantity(product_qty, product_id.uom_po_id)
        seller = product_id._select_seller(
            partner_id=partner,
            quantity=line.product_qty + procurement_uom_po_qty,
            date=line.order_id.date_order and line.order_id.date_order.date(),
            uom_id=product_id.uom_po_id)
        price_field = 'price_without_discount' if hasattr(seller, 'price_without_discount') else 'price'
        price_unit = self.env['account.tax']._fix_tax_included_price_company(seller[price_field],
                                                                             line.product_id.supplier_taxes_id,
                                                                             line.taxes_id,
                                                                             company_id) if seller else 0.0
        if price_unit and seller and line.order_id.currency_id and seller.currency_id != line.order_id.currency_id:
            price_unit = seller.currency_id._convert(
                price_unit, line.order_id.currency_id, line.order_id.company_id, fields.Date.today())
        res.update({
            'price_unit': price_unit
        })
        if hasattr(seller, 'first_discount'):
            res.update({
                'first_discount': seller.first_discount or 0.0
            })
        if hasattr(seller, 'second_discount'):
            res.update({
                'second_discount': seller.second_discount or 0.0
            })

        return res
