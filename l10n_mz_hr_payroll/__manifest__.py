{
    'name': 'Mozambican - Payroll',
    'description': """
        Mozambican Payroll Rules.
        
        * Calculate base using legal coeficient table
    """,

    'author': 'Arxi',
    'website': 'https://www.arxi.pt',

    'category': 'Human Resources/Payroll',
    'version': '15.0.0.1.5',
    'license': 'OPL-1',

    'depends': ['hr_payroll', 'l10n_mz'],

    'data': [
        'data/hr_payroll_structure_data.xml',
        'data/employee_salary_data.xml',
        'views/hr_employee_views.xml',
    ],

    'demo': [
    ],
}
