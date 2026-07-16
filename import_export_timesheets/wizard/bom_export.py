import base64
import io

import xlwt

from odoo import models, fields


class ExportBudgetSheet(models.TransientModel):
    _name = 'export.bom.sheet.wizard'
    _description = 'Export BOM Sheet Wizard'

    def print_bom_sheet_excel(self):
        active_id = self._context.get('active_id')
        bom_id = self.env['mrp.bom'].browse(active_id)
        workbook = xlwt.Workbook()
        title_style_comp = xlwt.easyxf(
            'align: horiz center ; font: name Times New Roman,bold off, italic off, height 450')
        title_style_comp_left = xlwt.easyxf(
            'align: horiz left ; font: name Times New Roman,bold off, italic off, height 450')
        title_style = xlwt.easyxf('align: horiz center ;font: name Times New Roman,bold off, italic off, height 350')
        title_style2 = xlwt.easyxf('font: name Times New Roman, height 200')
        title_style1 = xlwt.easyxf(
            'font: name Times New Roman,bold off, italic off, height 190; borders: top double, bottom double, left double, right double;')
        title_style1_table_head = xlwt.easyxf(
            'font: name Times New Roman,bold on, italic off, height 200; borders: top double, bottom double, left double, right double;')
        title_style1_table_head1 = xlwt.easyxf('font: name Times New Roman,bold on, italic off, height 200')
        title_style1_consultant = xlwt.easyxf(
            'font: name Times New Roman,bold on, italic off, height 200; borders: top double, bottom double, left double, right double;')
        title_style1_table_head_center = xlwt.easyxf(
            'align: horiz center ; font: name Times New Roman,bold on, italic off, height 190; borders: top thick, bottom thick, left thick, right thick;')

        title_style1_table_data = xlwt.easyxf(
            'align: horiz right ;font: name Times New Roman,bold on, italic off, height 190')
        title_style1_table_data_sub = xlwt.easyxf('font: name Times New Roman,bold off, italic off, height 190')
        title_style1_table_data_sub_amount = xlwt.easyxf(
            'align: horiz right ;font: name Times New Roman,bold off, italic off, height 190')
        title_style1_table_data_sub_balance = xlwt.easyxf(
            'align: horiz right ;font: name Times New Roman,bold off, italic off, height 190')
        sheet_name = 'Bom Sheet'
        sheet = workbook.add_sheet(sheet_name)

        product_tmpl_id = bom_id.product_tmpl_id
        product_id = bom_id.product_id
        product_qty = bom_id.product_qty
        product_uom_id = bom_id.product_uom_id
        routing_id = bom_id.routing_id
        code = bom_id.code
        bom_type = bom_id.type
        company_id = bom_id.company_id
        sheet.write(1, 0, 'Product', title_style1_table_head1)
        sheet.write(2, 0, product_tmpl_id.name, title_style1_table_data_sub)
        sheet.write(1, 1, 'Product Variant', title_style1_table_head1)
        if product_id:
            sheet.write(2, 1, product_id.name, title_style1_table_data_sub)
        else:
            sheet.write(2, 1, '', title_style1_table_data_sub)
        sheet.write(1, 2, 'Quantity', title_style1_table_head1)
        sheet.write(2, 2, product_qty, title_style1_table_data_sub)
        sheet.write(1, 3, 'Product Uom', title_style1_table_head1)
        sheet.write(2, 3, product_uom_id.name, title_style1_table_data_sub)
        column = sheet.col(4)
        column.width = 210 * 25
        sheet.write(1, 4, 'Routing', title_style1_table_head1)
        sheet.write(2, 4, routing_id.name, title_style1_table_data_sub)
        column = sheet.col(5)
        column.width = 210 * 25
        sheet.write(1, 5, 'Reference', title_style1_table_head1)
        if code:
            sheet.write(2, 5, code, title_style1_table_data_sub)
        else:
            sheet.write(2, 5, '', title_style1_table_data_sub)
        column = sheet.col(6)
        column.width = 210 * 25
        sheet.write(1, 6, 'Bom Type', title_style1_table_head1)
        if bom_id.type == 'normal':
            sheet.write(2, 6, 'Manufacture this product', title_style1_table_data_sub)
        else:
            sheet.write(2, 6, 'Kit', title_style1_table_data_sub)
        column = sheet.col(7)
        column.width = 210 * 50
        sheet.write(1, 7, 'Company', title_style1_table_head1)
        sheet.write(2, 7, company_id.name, title_style1_table_data_sub)

        sheet.write(5, 0, 'Component', title_style1_table_head)
        sheet.write(5, 1, 'Quantity', title_style1_table_head)
        sheet.write(5, 2, 'Product Unit of Measure', title_style1_table_head)
        sheet.write(5, 3, 'Consumed in Operation', title_style1_table_head)

        roww = 6

        bom_lines = bom_id.mapped("bom_line_ids")
        row_data = roww + 1
        for line in bom_lines:
            column = sheet.col(0)
            column.width = 210 * 25
            sheet.write(row_data, 0, line.product_id.name, title_style1_table_data_sub)
            column = sheet.col(1)
            column.width = 210 * 25
            sheet.write(row_data, 1, line.product_qty, title_style1_table_data_sub)
            column = sheet.col(2)
            column.width = 210 * 25
            sheet.write(row_data, 2, line.product_uom_id.name, title_style1_table_data_sub)
            column = sheet.col(3)
            column.width = 210 * 25
            if bom_id.type == 'normal':
                sheet.write(row_data, 3, line.operation_id.name, title_style1_table_data_sub)
            else:
                sheet.write(row_data, 3, '', title_style1_table_data_sub)
            row_data = row_data + 1
        roww = row_data + 3

        stream = io.BytesIO()
        workbook.save(stream)
        attach_id = self.env['bom.report.output.excel'].create({
            'name': 'Bom_sheet.xls',
            'xls_output': base64.encodestring(stream.getvalue())
        })
        return {
            'context': self.env.context,
            'view_mode': 'form',
            'res_model': 'bom.report.output.excel',
            'res_id': attach_id.id,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }


class BudgetReportOutputExcel(models.TransientModel):
    _name = 'bom.report.output.excel'
    _description = 'Wizard to store the Excel output'

    xls_output = fields.Binary(string='Excel Output', readonly=True)
    name = fields.Char(string='File Name', help='Save report as .xls format', )
