from odoo import models


class Payslip(models.Model):
    _inherit = 'hr.payslip'

    def _get_base_local_dict(self):
        res = super()._get_base_local_dict()
        res.update({
            'compute_irps': compute_irps,
        })
        return res

LOWER_LIMIT = 20250.00
UPPER_LIMIT = 144750.00
IRPS_DEPENDENTS_WAGES = ('20250.00', '20750.00', '21000.00', '21250.00', '21750.00', '22250.00', '32750.00', '60750.00', '144750.00')
IRPS_DEPENDENTS_COEFICIENTS = (
## 0 DEPENDENTS
    {
        '20750.00': (0.00, 0.10),
        '21000.00': (50.00, 0.10),
        '21250.00': (75.00, 0.10),
        '21750.00': (100.00, 0.10),
        '22250.00': (150.00, 0.10),
        '32750.00': (200.00, 0.15),
        '60750.00': (1775.00, 0.20),
        '144750.00': (7375.00, 0.25),
        'over': (28375.00, 0.32),
    },
## 1 DEPENDENTS
    {
        '21000.00': (0.00, 0.10),
        '21250.00': (25.00, 0.10),
        '21750.00': (50.00, 0.10),
        '22250.00': (100.00, 0.10),
        '32750.00': (150.00, 0.15),
        '60750.00': (1725.00, 0.20),
        '144750.00': (7325.00, 0.25),
        'over': (28325.00, 0.32),
    },
## 2 DEPENDENTS
    {
        '21250.00': (0.00, 0.10),
        '21750.00': (25.00, 0.10),
        '22250.00': (75.00, 0.10),
        '32750.00': (125.00, 0.15),
        '60750.00': (1700.00, 0.20),
        '144750.00': (7300.00, 0.25),
        'over': (28300.00, 0.32),
    },
## 3 DEPENDENTS
    {
        '21750.00': (0.00, 0.10),
        '22250.00': (50.00, 0.10),
        '32750.00': (100.00, 0.15),
        '60750.00': (1675.00, 0.20),
        '144750.00': (7275.00, 0.25),
        'over': (27275.00, 0.32),
    },
## 4+ DEPENDENTS
    {
        '22250.00': (0.00, 0.10),
        '32750.00': (50.00, 0.15),
        '60750.00': (1625.00, 0.20),
        '144750.00': (7225.00, 0.25),
        'over': (28225.00, 0.32),
    },
)

def calculate_irps(value, coeficient, base, lower_limit):
    return abs(value + (base - lower_limit) * coeficient)

def compute_irps(categories, employee):
    basic_category_code = categories.env.ref('hr_payroll.GROSS').code
    base = getattr(categories, basic_category_code)

    if base < LOWER_LIMIT:
        return 0.00

    nr_of_dependents = employee.children or 0
    if nr_of_dependents > 4:
        nr_of_dependents = 4

    if base >= UPPER_LIMIT:
        value_coeficient = IRPS_DEPENDENTS_COEFICIENTS[nr_of_dependents]['over']
        return calculate_irps(value_coeficient[0], value_coeficient[1], base, UPPER_LIMIT)

    for i, wage in enumerate(IRPS_DEPENDENTS_WAGES):
        if base < float(wage):
            if value_coeficient := IRPS_DEPENDENTS_COEFICIENTS[nr_of_dependents].get(wage):
                wage_index = IRPS_DEPENDENTS_WAGES.index(wage, 0)
                search_index = 0 if wage_index == 0 else wage_index - 1
                lower_limit = IRPS_DEPENDENTS_WAGES[search_index]
                return calculate_irps(value_coeficient[0], value_coeficient[1], base, float(lower_limit))

    return 0.00