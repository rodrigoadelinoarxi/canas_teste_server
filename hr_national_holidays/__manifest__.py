{
    'name'          : 'National Holidays',
    'summary'       : """Creates national holidays as a calendar resource time off.""",

    'author'        : "Arxi",
    'website'       : "http://www.arxi.pt",
    'category'      : 'Human Resources/Time Off',
    'version'       : '15.0.0.0.1',
    'license'       : 'OPL-1',
    'depends'       : ['hr_holidays'],
    'external_dependencies': {'python': ['holidays']},
    'data'          : [
        'security/ir.model.access.csv',
        'views/holiday_wizard_views.xml',
        'views/resource_calendar_views.xml'
    ],
}
