{
    'name': "Sale Cancel With Reason",

    'summary': """
        Allows canceling sales and storing a cancelling reason.""",
    'author': "Arxi",
    'website': "https://www.arxi.pt",
    'category': 'Sales',
    'version': '15.0.0.0.2',
    'license': 'OPL-1',
    'depends': ['sale_management'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/sale_reason_wizard_views.xml',
        'views/sale_order_views.xml'
    ],
    "auto_install": True,
}
