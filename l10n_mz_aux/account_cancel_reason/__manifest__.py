{
    'name': "Account Cancel With Reason",

    'summary': """
        Allows canceling accounting entries and storing a cancelling reason.""",
    'author': "Arxi",
    'website': "https://www.arxi.pt",
    'category': 'Accounting',
    'version': '15.0.0.0.4',
    'license': 'OPL-1',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'views/cancel_invoice_wizard_views.xml',
        'views/account_payment_views.xml',
        'views/account_move_views.xml',
        'report/account_move_templates.xml',
        'report/account_payment_templates.xml'
    ],
    'auto_install': True,
    'application': False,
}
