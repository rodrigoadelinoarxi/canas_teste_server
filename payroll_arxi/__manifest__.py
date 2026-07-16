{
    'name': 'Payroll Arxi',
    'summary': """Implements several fields to payroll to implement structure""",

    'author': 'Arxi',
    'website': 'https://www.arxi.pt',
    'sequence': 51,

    'category': 'Human Resources/Payroll',
    'version': '15.0.0.0.86',
    'license': 'OPL-1',

    'depends': ['hr_payroll_account', 'l10n_mz_hr_payroll', 'hr_contract', 'hr_holidays', 'hr_work_entry_contract_enterprise', 'project'],

    'data': [
        'security/ir.model.access.csv',
        'data/hr_payroll_data.xml',
        'data/hr_payroll_structure_data.xml',
        'data/employee_salary_data.xml',
        'data/hr_leave_type_data.xml',
        'data/hr_payslip_input_type_data.xml',
        'data/cron.xml',
        'wizard/update_allowances_wizard_views.xml',
        'wizard/work_entry_regeneration_wizard_views.xml',
        'views/hr_contract_history_report_views.xml',
        'views/hr_employee_views.xml',
        'views/res_company_views.xml',
        'views/hr_payslip_views.xml',
        'views/allowance_line_views.xml',
        'views/hr_salary_attachment.xml',
        'views/hr_payslip_run_views.xml',
    ],
}
