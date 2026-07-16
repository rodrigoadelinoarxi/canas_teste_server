{
    'name': "Canas",

    'summary': """
        Módulo de configurações e desenvolvimentos base para o ARXI/Canas.""",
    'sequence': 404,
    'author': "Arxi",
    'website': "https://www.arxi.pt",
    'category': 'Uncategorized',
    'version': '15.0.0.2.29',
    'license': 'OPL-1',
    'assets': {
        'web.assets_backend': [
            'canas/static/src/js/**/*',
        ],
    },
    'depends': [
        'fleet', 'project', 'purchase', 'account', 'hr_expense', 'account_accountant', 'sale_management',
        'repair_fleet_integration', 'import_export_timesheets', 'repair', 'hr_contract', 'purchase_line_discount',
        'hr_national_holidays', 'hr_holidays', 'hr_work_entry_contract', 'hr_payroll'
    ],
    'data': [
        'security/ir.model.access.csv',
        'security/res_groups.xml',

        'data/project_data.xml',
        'data/partner_data.xml',
        'data/hr_leave_type_data.xml',
        'data/hr_work_entry_type.xml',

        'views/product_views.xml',
        'views/res_partner_views.xml',
        'views/fleet_vehicle_views.xml',
        'views/project_views.xml',
        'views/purchase_views.xml',
        'views/hr_views.xml',
        'views/repair_views.xml',
        'views/report_invoice.xml',
        'views/hr_contract_views.xml',
        'views/hr_payslip_views.xml',
        'views/hr_work_entry.xml',

        'report/hr_payslips_report.xml',
        'report/purchase_order_report.xml',
        'report/report_templates.xml',

    ],
}
