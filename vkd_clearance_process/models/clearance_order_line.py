from odoo import _, api, fields, models


class ClearanceOrderLine(models.Model):
    _name = 'clearance.order.line'
    _description = 'Clearance Order Line'

    name = fields.Char(
        string="Name",
        required=True, copy=False, readonly=False,
        index='trigram',
        default=lambda self: _('New'))
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Customer",
        change_default=True, index=True,
        tracking=1,
        domain="[('company_id', 'in', (False, company_id))]")
    clearance_sale_order_id = fields.Many2one('sale.order')
    container_no = fields.Char(string='Container No.')
    number_of_package = fields.Float(string='Number of Packages')
    volume = fields.Float(string='Volume (CBM)')
    weight = fields.Float(string='Weight (Kg)')
    arrival_date = fields.Date(string='Arrival Date')
    cleared_date = fields.Date(string='Cleared Date')
    container_returned_date = fields.Date(string='Returned Date')
    loaded_to = fields.Char(string='Loaded To')
    container_type = fields.Selection([('box', 'Box'),
                                       ('loose', 'Loose')], string='Clearance Type', required=True)