from odoo import fields, models, _


class RentalExtendHistory(models.Model):
    _name = 'rental.extend.history'

    rental_order_id = fields.Many2one('sale.order', string="Rental Order", ondelete='cascade')
    start_date = fields.Datetime(string="Start Date")
    return_date = fields.Datetime(string="Return Date")
    reason = fields.Text(string="Reason for Extension")