import logging

from odoo import api, fields, models
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_round

_logger = logging.getLogger(__name__)


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.onchange('partner_id')
    def _onchange_quantity(self):
        for line in self.order_line:
            line._onchange_quantity()

    def _prepare_supplier_info(self, partner, line, price, currency):
        # Prepare supplierinfo data when adding a product and using the price_without_discount and discount fields
        return {
            'name'       : partner.id,
            'sequence'   : max(
                line.product_id.seller_ids.mapped('sequence')) + 1 if line.product_id.seller_ids else 1,
            'min_qty'    : 0.0,
            'price_without_discount': price,
            'first_discount': line.first_discount,
            'second_discount': line.second_discount,
            'currency_id': currency.id,
            'delay'      : 0,
        }


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    first_discount = fields.Float(string='First Discount (%)', digits='Discount')
    second_discount = fields.Float(string='Second Discount (%)', digits='Discount')

    _sql_constraints = [
        ('first_discount_check', 'CHECK (first_discount>=0 AND first_discount<=100)',
         'The discount must be between 0 and 100.'),
        ('second_discount_check', 'CHECK (second_discount>=0 AND second_discount<=100)',
         'The discount must be between 0 and 100.'),
    ]

    @api.depends('product_qty', 'price_unit', 'taxes_id', 'first_discount', 'second_discount')
    def _compute_amount(self):
        return super(PurchaseOrderLine, self)._compute_amount()

    def _prepare_compute_all_values(self):
        res = super(PurchaseOrderLine, self)._prepare_compute_all_values()
        res['price_unit'] = self.get_final_price()
        return res

    def get_final_price(self):
        price_unit = self.price_unit
        discount_list = []
        if price_unit > 0:
            if self.first_discount > 0:
                discount_list.append(self.first_discount)
            if self.second_discount > 0:
                discount_list.append(self.second_discount)
            for discount in discount_list:
                price_unit = ((100 - discount) * price_unit) / 100
        return price_unit

    def _prepare_purchase_order_line_from_procurement(self, product_id, product_qty, product_uom, company_id, values, po):
        res = super(PurchaseOrderLine, self)._prepare_purchase_order_line_from_procurement(product_id, product_qty, product_uom, company_id, values, po)
        procurement_uom_po_qty = product_uom._compute_quantity(product_qty, product_id.uom_po_id)
        seller = product_id._select_seller(
            partner_id=po.partner_id,
            quantity=procurement_uom_po_qty,
            date=po.date_order and po.date_order.date(),
            uom_id=product_id.uom_po_id)
        taxes = product_id.supplier_taxes_id
        fpos = po.fiscal_position_id
        taxes_id = fpos.map_tax(taxes, product_id, seller.name) if fpos else taxes
        price_field = 'price_without_discount' if hasattr(seller, 'price_without_discount') else 'price'
        price_unit = self.env['account.tax']._fix_tax_included_price_company(seller[price_field],
                                                                             product_id.supplier_taxes_id, taxes_id,
                                                                             po.company_id) if seller else 0.0
        if price_unit and seller and po.currency_id and seller.currency_id != po.currency_id:
            price_unit = seller.currency_id._convert(
                price_unit, po.currency_id, po.company_id, po.date_order or fields.Date.today())
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

    def _prepare_account_move_line(self, move=False):
        data = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        discount = self.first_discount + self.second_discount - (
                    (self.first_discount * self.second_discount) / 100) or self.second_discount
        data['discount'] = discount
        return data

    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        super(PurchaseOrderLine, self)._onchange_quantity()
        if not self.product_id:
            return
        params = {'order_id': self.order_id}
        seller = self.product_id._select_seller(
            partner_id=self.partner_id,
            quantity=self.product_qty,
            date=self.order_id.date_order and self.order_id.date_order.date(),
            uom_id=self.product_uom,
            params=params)

        if seller or not self.date_planned:
            self.date_planned = self._get_date_planned(seller).strftime(DEFAULT_SERVER_DATETIME_FORMAT)

        if not seller or seller.name != self.order_id.partner_id:
            self.first_discount = self.second_discount = 0
            return

        price_unit = self.env['account.tax']._fix_tax_included_price_company(seller.price_without_discount,
                                                                             self.product_id.supplier_taxes_id,
                                                                             self.taxes_id,
                                                                             self.company_id) if seller else 0.0
        if price_unit and seller and self.order_id.currency_id and seller.currency_id != self.order_id.currency_id:
            price_unit = seller.currency_id._convert(
                price_unit, self.order_id.currency_id, self.order_id.company_id, self.date_order or fields.Date.today())

        if seller and self.product_uom and seller.product_uom != self.product_uom:
            price_unit = seller.product_uom._compute_price(price_unit, self.product_uom)

        self.price_unit = price_unit
        self.first_discount = seller.first_discount
        self.second_discount = seller.second_discount

    def _get_stock_move_price_unit(self):
        """
        Price unit calculation for stock quant valuation needs to consider the discount
        """
        self.ensure_one()
        order = self.order_id
        # Overriden here
        discounts = (1 - (self.first_discount or 0.0) / 100.0) * (1 - (self.second_discount or 0.0) / 100.0)
        price_unit = self.price_unit * discounts
        price_unit_prec = self.env['decimal.precision'].precision_get('Product Price')
        if self.taxes_id:
            qty = self.product_qty or 1
            price_unit = self.taxes_id.with_context(round=False).compute_all(
                price_unit, currency=self.order_id.currency_id, quantity=qty, product=self.product_id,
                partner=self.order_id.partner_id
            )['total_void']
            price_unit = float_round(price_unit / qty, precision_digits=price_unit_prec)
        if self.product_uom.id != self.product_id.uom_id.id:
            price_unit *= self.product_uom.factor / self.product_id.uom_id.factor
        if order.currency_id != order.company_id.currency_id:
            price_unit = order.currency_id._convert(
                price_unit, order.company_id.currency_id, self.company_id, self.date_order or fields.Date.today(),
                round=False)
        return price_unit
