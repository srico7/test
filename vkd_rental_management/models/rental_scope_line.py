from odoo import fields, models, _


class RentalScopeLine(models.Model):
    _name = 'rental.scope.line'

    name = fields.Char(string='Name')
    description = fields.Char(string='Description', required=True)
    rental_id = fields.Many2one(comodel_name='rental.job')
    sale_order_id = fields.Many2one(comodel_name='sale.order')
