{
    'name': "Mozambican - Accounting",

    'summary': """
        Mozambican Accounting Module""",
    'author': "Arxi",
    'website': "https://www.arxi.pt",
    'category': 'Localization',
    'version': '15.0.0.0.3',
    'depends': ['account'],
    'license': 'OPL-1',
    'data': [
        'data/account_chart_template.xml',
        'data/account_account_template.xml',
        'data/account_chart_template_upd.xml',
        'data/account_tax_data.xml',
        'data/account_chart_configure_data.xml',
    ],
}
# TODO fazer um pre-init para tratar do imposto já criado em base de dados, EXTERNAL ID
