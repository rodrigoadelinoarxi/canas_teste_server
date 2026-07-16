from . import models


def post_init_hook(cr, registry):
    cr.execute("""UPDATE product_supplierinfo SET price_without_discount = price 
    WHERE first_discount = 0 AND second_discount = 0""")
