{
    'name': "Purchase Line Discount",
    'summary': """
        Add discounts in purchase lines""",
    'author': "ARXILEAD",
    'website': "https://www.arxi.pt",
    'category': 'Uncategorized',
    'version': '15.0.0.0.1',
    'license': 'OPL-1',
    'depends': ['sale_purchase', 'stock', 'purchase_stock', 'supplierinfo_discounts'],
    'data': [
        'views/purchase_view.xml',
        'reports/purchase_order_report.xml'
    ],
}
