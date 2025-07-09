from odoo import _, api, fields, models


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    is_clearance = fields.Boolean(string='Is Clearance', related='order_id.is_clearance')
    container_no = fields.Char(string='Container No.')
    number_of_package = fields.Float(string='Number of Packages')
    volume = fields.Float(string='Volume (CBM)')
    weight = fields.Float(string='Weight (Kg)')
    arrival_date = fields.Datetime(string='Arrival Date')
    cleared_date = fields.Date(string='Cleared Date')
    discharge_date = fields.Date(string='Discharge Date')
    container_returned_date = fields.Date(string='Returned Date')
    loaded_to = fields.Char(string='Loaded To')
    container_type = fields.Selection([('box', 'Box'),
                                       ('loose', 'Loose')], string='Clearance Type', required=True)
    clearance_mode = fields.Selection([('lorry', 'Lorry'),
                                       ('trailer', 'Trailer'),
                                       ('dhoni', 'Dhoni')], string='Clearance Mode')
    clearance_location = fields.Selection([('male', 'Male'),
                                           ('hulumale', 'Hulumale')], string='Clearance Location')
    bl_number = fields.Char(string='BL Number', copy=False)

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        res = super(SaleOrderLine, self)._action_launch_stock_rule()
        for rec in self:
            for line in rec.order_id.picking_ids:
                line.clearance_sale_order = rec.order_id
                line.is_clearance = rec.is_clearance
        return res

