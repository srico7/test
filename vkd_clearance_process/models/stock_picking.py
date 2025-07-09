from odoo import _, api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'


    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Pending Arrival'),
        ('done', 'Arrived'),
        ('approve', 'Approved'),
        ('cancel', 'Cancelled'),
    ], string='Status')
    clearance_sale_order = fields.Many2one('sale.order')
    is_clearance = fields.Boolean(default=False)