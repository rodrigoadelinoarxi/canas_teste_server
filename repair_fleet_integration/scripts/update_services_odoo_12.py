fuel_service = self.env.ref('repair_fleet_integration.fuel_service')
repair_service = self.env.ref('repair_fleet_integration.repair_service')

for rec_cost in self.env['fleet.vehicle.cost'].search([]).filtered(lambda c: c.cost_subtype_id == repair_service):
    self.env['fleet.vehicle.log.services'].create({
        'vehicle_id': rec_cost.vehicle_id.id,
        'amount': rec_cost.amount,
        'date': rec_cost.date,
        'cost_subtype_id': repair_service.id,
    })

for rec_fuel in self.env['fleet.vehicle.log.fuel'].search([]):
    self.env['fleet.vehicle.log.services'].create({
        'vehicle_id': rec_fuel.vehicle_id.id,
        'amount': rec_fuel.amount,
        'odometer': rec_fuel.odometer,
        'date': rec_fuel.date,
        'cost_subtype_id': fuel_service.id,
        'vendor_id': rec_fuel.vendor_id.id,
        'liter': rec_fuel.liter,
        'price_per_liter': rec_fuel.price_per_liter,
    })

import csv


def import_vehicle_status(path):
    # with open(r'/home/administrator/PycharmProjects/server-casperventures/casperventures/Plano Contas Casper v2 2014.csv', newline='') as csvfile:
    with open(path, newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',', quotechar='"')
        next(reader)  # header
        for row in reader:
            if not row[1] or row[1] == 'Data':
                continue
            vehicle_id = self.env['fleet.vehicle'].browse(int(row[3]))
            if row[5] == 'COST':
                self.env['fleet.vehicle.log.services'].sudo().create({
                    'service_type_id': self.env.ref('repair_fleet_integration.cost_service').id,
                    'date': row[1],
                    'amount': row[0],
                    'vehicle_id': vehicle_id.id,
                })
            else:
                self.env['fleet.vehicle.odometer'].sudo().create({
                    'date': row[1],
                    'value': row[0],
                    'vehicle_id': vehicle_id.id,
                    'unit': self.env.ref('uom.product_uom_km').id
                })
