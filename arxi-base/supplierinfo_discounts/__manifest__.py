{
    'name'          : "Supplierinfo Discounts",

    'summary'       : """Add discounts in supplierinfo""",
    'author'        : "ARXILEAD",
    'website'       : "https://www.arxi.pt",
    'category'      : 'Uncategorized',
    'version'       : '15.0.0.0.1',
    'license'       : 'OPL-1',
    'depends'       : ['product'],
    'data'          : [
        'views/product_supplierinfo.xml',
    ],
    'post_init_hook': 'post_init_hook'
}
