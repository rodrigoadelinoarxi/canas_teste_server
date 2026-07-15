{
	'name': 'Import Export Timesheets',

	'summary': """Allows Importing/Exporting of Timesheets""",
	'author': 'Arxi',
	'website': 'https://www.arxi.pt',
	'category': 'Timesheets',
	'version': '15.0.0.0.2',
	'license': 'OPL-1',
	'external_dependencies': {
		'python': ['xlrd']
	},
	'depends': ['project', 'hr_timesheet', 'repair_fleet_integration'],
	'data': [
		'security/ir.model.access.csv',
		'wizard/timesheets_line_import.xml',
		'views/timesheets_line_import_view.xml',
		'data/account_analytic_tag_data.xml',
		'wizard/filosoft_export_wizard.xml'
	],
	'installable': True,
	'application': False,
}
